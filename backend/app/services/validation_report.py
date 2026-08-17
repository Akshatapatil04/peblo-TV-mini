import json
import os
from typing import Dict, List, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.show import Show
from backend.app.models.season import Season
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork

# Load reference config
REFERENCE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../seed_data/reference.json"))
with open(REFERENCE_PATH, "r", encoding="utf-8") as f:
    REFERENCE_DATA = json.load(f)

ALLOWED_SECTIONS = set(REFERENCE_DATA.get("sections", ["featured", "series", "minisodes", "songs"]))
ALLOWED_CATEGORIES = set(REFERENCE_DATA.get("categories", []))
ALLOWED_LANGUAGES = set(REFERENCE_DATA.get("languages", ["en", "hi"]))

async def generate_validation_report(db: AsyncSession) -> Dict[str, Any]:
    """
    Scans the database and generates a complete, editor-friendly validation report.
    Identifies all issues blocking publish as well as non-blocking warnings.
    """
    # Fetch all shows with seasons, episodes, and artworks
    query = (
        select(Show)
        .options(
            selectinload(Show.seasons).selectinload(Season.episodes).selectinload(Episode.artworks),
            selectinload(Show.episodes).selectinload(Episode.artworks),
            selectinload(Show.artworks)
        )
        .order_by(Show.title)
    )
    result = await db.execute(query)
    shows: List[Show] = result.scalars().all()

    blocking_errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    grouped_by_show: Dict[str, Dict[str, Any]] = {}

    # Check 1: Duplicate (content_group, language) across all episodes
    dup_query = (
        select(
            Episode.content_group,
            Episode.language,
            func.count(Episode.id).label("count")
        )
        .group_by(Episode.content_group, Episode.language)
        .having(func.count(Episode.id) > 1)
    )
    dup_res = await db.execute(dup_query)
    duplicates = dup_res.all()

    duplicate_pairs = {(row.content_group, row.language): row.count for row in duplicates}

    for show in shows:
        show_blockers = []
        show_warnings = []

        show_has_poster = any(a.slot_type == "poster" for a in show.artworks)
        show_has_banner = any(a.slot_type == "banner" for a in show.artworks)

        # Show-level checks
        if show.status == "published":
            # Section check
            if not show.section:
                err = {
                    "entity_type": "show",
                    "entity_id": show.id,
                    "show_id": show.id,
                    "show_slug": show.slug,
                    "show_title": show.title,
                    "title": show.title,
                    "field": "section",
                    "severity": "blocking",
                    "message": f"Published show '{show.title}' has no section assigned.",
                    "remediation": f"Assign one of the allowed sections: {', '.join(sorted(ALLOWED_SECTIONS))}."
                }
                blocking_errors.append(err)
                show_blockers.append(err)
            elif show.section not in ALLOWED_SECTIONS:
                err = {
                    "entity_type": "show",
                    "entity_id": show.id,
                    "show_id": show.id,
                    "show_slug": show.slug,
                    "show_title": show.title,
                    "title": show.title,
                    "field": "section",
                    "severity": "blocking",
                    "message": f"Show '{show.title}' has invalid section '{show.section}'.",
                    "remediation": f"Change section to one of: {', '.join(sorted(ALLOWED_SECTIONS))}."
                }
                blocking_errors.append(err)
                show_blockers.append(err)

            # Show artwork check (warning if missing poster/banner)
            if not show_has_poster or not show_has_banner:
                warn = {
                    "entity_type": "show",
                    "entity_id": show.id,
                    "show_id": show.id,
                    "show_slug": show.slug,
                    "show_title": show.title,
                    "title": show.title,
                    "field": "artwork",
                    "severity": "warning",
                    "message": f"Show '{show.title}' is missing recommended artwork (Poster or Banner).",
                    "remediation": "Upload high-resolution poster (2:3) and hero banner (16:9) for optimal viewer experience."
                }
                warnings.append(warn)
                show_warnings.append(warn)
        else:
            show_warnings.append({
                "entity_type": "show",
                "entity_id": show.id,
                "show_id": show.id,
                "show_slug": show.slug,
                "show_title": show.title,
                "title": show.title,
                "field": "status",
                "severity": "info",
                "message": f"Show '{show.title}' is currently in 'draft' status and will not appear in published catalogue.",
                "remediation": "Change status to 'published' when ready to release."
            })

        # Category check
        invalid_categories = [c for c in (show.categories or []) if c not in ALLOWED_CATEGORIES]
        if invalid_categories:
            err = {
                "entity_type": "show",
                "entity_id": show.id,
                "show_id": show.id,
                "show_slug": show.slug,
                "show_title": show.title,
                "title": show.title,
                "field": "categories",
                "severity": "blocking" if show.status == "published" else "warning",
                "message": f"Show '{show.title}' contains invalid categories: {', '.join(invalid_categories)}.",
                "remediation": f"Allowed categories are: {', '.join(sorted(ALLOWED_CATEGORIES))}."
            }
            if show.status == "published":
                blocking_errors.append(err)
                show_blockers.append(err)
            else:
                warnings.append(err)
                show_warnings.append(err)

        # Episode-level checks
        for episode in show.episodes:
            ep_artworks = episode.artworks or []
            has_artwork = len(ep_artworks) > 0

            # Check duplicate (content_group, language)
            pair = (episode.content_group, episode.language)
            if pair in duplicate_pairs and duplicate_pairs[pair] > 1:
                err = {
                    "entity_type": "episode",
                    "entity_id": episode.episode_id or episode.id,
                    "db_id": episode.id,
                    "show_id": show.id,
                    "show_slug": show.slug,
                    "show_title": show.title,
                    "title": f"S{episode.season_number:02d}E{episode.episode_number:02d} - {episode.episode_title}",
                    "field": "content_group",
                    "severity": "blocking",
                    "message": (
                        f"Duplicate language variant: Episode '{episode.episode_title}' ({episode.episode_id}) has "
                        f"content_group '{episode.content_group}' and language '{episode.language}', which is duplicated "
                        f"by {duplicate_pairs[pair]} episodes."
                    ),
                    "remediation": "Each language variant within a content_group must be unique. Update the language code or content_group."
                }
                blocking_errors.append(err)
                show_blockers.append(err)

            if episode.status == "published":
                # Rule: An episode cannot be published without duration > 0
                if not episode.duration_seconds or episode.duration_seconds <= 0:
                    err = {
                        "entity_type": "episode",
                        "entity_id": episode.episode_id or episode.id,
                        "db_id": episode.id,
                        "show_id": show.id,
                        "show_slug": show.slug,
                        "show_title": show.title,
                        "title": f"S{episode.season_number:02d}E{episode.episode_number:02d} - {episode.episode_title}",
                        "field": "duration_seconds",
                        "severity": "blocking",
                        "message": f"Published episode '{episode.episode_title}' ({episode.episode_id}) has invalid or missing duration ({episode.duration_seconds}s).",
                        "remediation": "Enter a valid positive duration in seconds (e.g., 300s)."
                    }
                    blocking_errors.append(err)
                    show_blockers.append(err)

                # Rule: An episode cannot be published without artwork
                if not has_artwork:
                    err = {
                        "entity_type": "episode",
                        "entity_id": episode.episode_id or episode.id,
                        "db_id": episode.id,
                        "show_id": show.id,
                        "show_slug": show.slug,
                        "show_title": show.title,
                        "title": f"S{episode.season_number:02d}E{episode.episode_number:02d} - {episode.episode_title}",
                        "field": "artwork",
                        "severity": "blocking",
                        "message": f"Published episode '{episode.episode_title}' ({episode.episode_id}) is missing artwork.",
                        "remediation": "Upload a 16:9 thumbnail for this episode or ensure show-level artwork is provided."
                    }
                    blocking_errors.append(err)
                    show_blockers.append(err)

                # Language validity
                if episode.language not in ALLOWED_LANGUAGES:
                    err = {
                        "entity_type": "episode",
                        "entity_id": episode.episode_id or episode.id,
                        "db_id": episode.id,
                        "show_id": show.id,
                        "show_slug": show.slug,
                        "show_title": show.title,
                        "title": f"S{episode.season_number:02d}E{episode.episode_number:02d} - {episode.episode_title}",
                        "field": "language",
                        "severity": "blocking",
                        "message": f"Episode '{episode.episode_title}' has unsupported language '{episode.language}'.",
                        "remediation": f"Allowed languages are: {', '.join(sorted(ALLOWED_LANGUAGES))}."
                    }
                    blocking_errors.append(err)
                    show_blockers.append(err)

        grouped_by_show[show.id] = {
            "show_id": show.id,
            "show_slug": show.slug,
            "show_title": show.title,
            "status": show.status,
            "section": show.section,
            "blocking_count": len(show_blockers),
            "warning_count": len(show_warnings),
            "errors": show_blockers,
            "warnings": show_warnings
        }

    can_publish = len(blocking_errors) == 0

    return {
        "can_publish": can_publish,
        "total_shows": len(shows),
        "total_blocking_errors": len(blocking_errors),
        "total_warnings": len(warnings),
        "blocking_errors": blocking_errors,
        "warnings": warnings,
        "grouped_by_show": grouped_by_show
    }
