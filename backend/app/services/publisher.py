import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.show import Show
from backend.app.models.season import Season
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork
from backend.app.models.publish_run import PublishRun
from backend.app.services.storage import get_storage
from backend.app.services.validation_report import generate_validation_report, ALLOWED_SECTIONS

class PublishError(Exception):
    """Exception raised when a publish job cannot proceed."""
    pass

async def execute_publish(
    db: AsyncSession,
    initiated_by: str = "admin",
    force: bool = False
) -> Dict[str, Any]:
    """
    Executes an atomic publish run:
    1. Validates catalogue readiness (unless forced).
    2. Builds normalized catalogue JSON according to Peblo TV specifications:
       - Only published shows & episodes.
       - Language variants with same content_group collapse into one entry with `languages: [...]`.
       - Season 0 trailers isolated in `trailers: [...]` instead of regular seasons.
       - Deterministic sorting by section, show, season, episode.
    3. Atomically writes the catalogue file to storage.
    4. Records the run in DB.
    """
    started_at = datetime.now(timezone.utc)
    version = f"v_{started_at.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    # 1. Validation check
    validation = await generate_validation_report(db)
    if not force and not validation["can_publish"]:
        error_msg = f"Publish blocked by {validation['total_blocking_errors']} critical issue(s)."
        # Record failed run
        failed_run = PublishRun(
            initiated_by=initiated_by,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            status="failed",
            error_message=error_msg,
            catalogue_version=version
        )
        db.add(failed_run)
        await db.commit()
        raise PublishError(error_msg)

    # 2. Query published shows with published episodes
    query = (
        select(Show)
        .where(Show.status == "published")
        .options(
            selectinload(Show.seasons).selectinload(Season.episodes).selectinload(Episode.artworks),
            selectinload(Show.episodes).selectinload(Episode.artworks),
            selectinload(Show.artworks)
        )
        .order_by(Show.title)
    )
    result = await db.execute(query)
    published_shows: List[Show] = result.scalars().all()

    # Define deterministic section order
    section_order = ["featured", "series", "minisodes", "songs"]
    for s in ALLOWED_SECTIONS:
        if s not in section_order:
            section_order.append(s)

    sections_dict: Dict[str, List[Dict[str, Any]]] = {s: [] for s in section_order}
    total_shows_count = 0
    total_episodes_count = 0

    for show in published_shows:
        if not show.section or show.section not in sections_dict:
            continue

        # Show artworks
        show_artworks = {
            a.slot_type: a.url for a in (show.artworks or [])
        }

        # Separate Season 0 (Trailers) from regular seasons
        regular_seasons_data: List[Dict[str, Any]] = []
        trailers_data: List[Dict[str, Any]] = []

        # Sort seasons by season_number ascending
        sorted_seasons = sorted(show.seasons, key=lambda s: s.season_number)

        for season in sorted_seasons:
            # Filter published episodes only
            published_eps = [e for e in season.episodes if e.status == "published"]
            if not published_eps:
                continue

            # Group episodes by content_group to collapse language variants!
            grouped_episodes: Dict[str, List[Episode]] = {}
            for ep in published_eps:
                grouped_episodes.setdefault(ep.content_group, []).append(ep)

            collapsed_episode_list: List[Dict[str, Any]] = []

            for content_group, eps in grouped_episodes.items():
                # Sort variants by language for determinism
                eps_sorted = sorted(eps, key=lambda e: e.language)
                primary_ep = eps_sorted[0]

                # Collect all available languages
                languages = sorted(list({e.language for e in eps_sorted}))

                # Collect all available audio variants metadata
                audio_variants = [
                    {
                        "language": e.language,
                        "episode_id": e.episode_id or e.id,
                        "duration_seconds": e.duration_seconds,
                        "title": e.episode_title,
                        "synopsis": e.synopsis
                    }
                    for e in eps_sorted
                ]

                # Collect episode artwork or fallback to show artwork
                ep_artworks = {}
                for e in eps_sorted:
                    for a in (e.artworks or []):
                        ep_artworks[a.slot_type] = a.url

                # Inherit show poster/banner if episode only has thumbnail
                artwork_payload = {
                    "poster": ep_artworks.get("poster") or show_artworks.get("poster"),
                    "banner": ep_artworks.get("banner") or show_artworks.get("banner"),
                    "thumbnail": ep_artworks.get("thumbnail") or show_artworks.get("thumbnail") or ep_artworks.get("banner") or show_artworks.get("banner")
                }

                collapsed_entry = {
                    "content_group": content_group,
                    "episode_number": primary_ep.episode_number,
                    "title": primary_ep.episode_title,
                    "synopsis": primary_ep.synopsis or show.synopsis,
                    "duration_seconds": primary_ep.duration_seconds,
                    "languages": languages,
                    "audio_variants": audio_variants,
                    "artwork": artwork_payload
                }

                collapsed_episode_list.append(collapsed_entry)
                total_episodes_count += 1

            # Sort collapsed episodes by episode_number ascending
            collapsed_episode_list.sort(key=lambda e: e["episode_number"])

            if season.season_number == 0:
                # Season 0 is reserved for trailers — store directly under show.trailers
                trailers_data.extend(collapsed_episode_list)
            else:
                regular_seasons_data.append({
                    "season_number": season.season_number,
                    "title": season.title or f"Season {season.season_number}",
                    "episodes_count": len(collapsed_episode_list),
                    "episodes": collapsed_episode_list
                })

        show_entry = {
            "id": show.id,
            "slug": show.slug,
            "title": show.title,
            "synopsis": show.synopsis,
            "section": show.section,
            "categories": show.categories or [],
            "artwork": {
                "poster": show_artworks.get("poster"),
                "banner": show_artworks.get("banner"),
                "thumbnail": show_artworks.get("thumbnail")
            },
            "trailers": trailers_data,
            "seasons": regular_seasons_data,
            "total_seasons": len(regular_seasons_data)
        }

        sections_dict[show.section].append(show_entry)
        total_shows_count += 1

    # Filter out empty sections or preserve standard sections
    sections_output = []
    for s_name in section_order:
        shows_in_sec = sections_dict.get(s_name, [])
        # Deterministic sort shows by title
        shows_in_sec.sort(key=lambda x: x["title"])
        sections_output.append({
            "section_id": s_name,
            "title": s_name.capitalize(),
            "shows_count": len(shows_in_sec),
            "shows": shows_in_sec
        })

    # Top-level catalogue envelope
    catalogue_envelope = {
        "schema_version": "1.0",
        "catalogue_version": version,
        "generated_at": started_at.isoformat(),
        "summary": {
            "total_sections": len(sections_output),
            "total_shows": total_shows_count,
            "total_episodes": total_episodes_count
        },
        "sections": sections_output
    }

    # 3. Atomically write to storage
    content_bytes = json.dumps(catalogue_envelope, indent=2, ensure_ascii=False).encode("utf-8")
    storage = get_storage()

    # Main live catalogue key (atomic replace)
    live_key = "catalog/catalogue.json"
    catalogue_url = await storage.atomic_write(live_key, content_bytes, content_type="application/json")

    # History snapshot for rollback
    history_key = f"catalog/history/catalogue_{version}.json"
    await storage.save(content_bytes, history_key, content_type="application/json")

    completed_at = datetime.now(timezone.utc)

    # 4. Record successful publish run
    publish_run = PublishRun(
        initiated_by=initiated_by,
        started_at=started_at,
        completed_at=completed_at,
        status="success",
        shows_count=total_shows_count,
        episodes_count=total_episodes_count,
        sections_count=len(sections_output),
        catalogue_path=live_key,
        catalogue_version=version,
        catalogue_data=catalogue_envelope
    )
    db.add(publish_run)
    await db.commit()
    await db.refresh(publish_run)

    return {
        "run_id": publish_run.id,
        "version": version,
        "status": "success",
        "shows_count": total_shows_count,
        "episodes_count": total_episodes_count,
        "sections_count": len(sections_output),
        "catalogue_url": catalogue_url,
        "published_at": completed_at.isoformat()
    }
