import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.show import Show
from backend.app.models.season import Season
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork
from backend.app.services.storage import get_storage
from backend.app.schemas.catalog import SearchResponse, SearchShowResult

router = APIRouter(prefix="/catalog", tags=["Viewer Catalog"])

@router.get("", response_model=Dict[str, Any])
async def get_published_catalog(response: Response):
    """
    Fast viewer endpoint that serves the pre-published catalogue file from storage.
    Includes cache headers for client-side and CDN caching.
    """
    storage = get_storage()
    catalog_key = "catalog/catalogue.json"
    
    try:
        content_bytes = await storage.get(catalog_key)
        catalog_data = json.loads(content_bytes.decode("utf-8"))
        
        # Add caching headers
        response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
        response.headers["ETag"] = f'"{catalog_data.get("catalogue_version", "v1")}"'
        return catalog_data
    except Exception:
        # If no published catalogue exists yet, return empty structure
        return {
            "schema_version": "1.0",
            "catalogue_version": "initial",
            "generated_at": None,
            "summary": {
                "total_sections": 0,
                "total_shows": 0,
                "total_episodes": 0
            },
            "sections": [],
            "message": "No published catalogue yet. An admin must run publish from the CMS."
        }

@router.get("/search", response_model=SearchResponse)
async def search_catalog(
    db: AsyncSession = Depends(get_db),
    q: Optional[str] = Query(None, description="Search term matching show title, episode title, or categories"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. adventure, india)"),
    language: Optional[str] = Query(None, description="Filter by audio language (en, hi)"),
    section: Optional[str] = Query(None, description="Filter by section (featured, series, minisodes, songs)")
):
    """
    Composable search endpoint:
    - `q` matches show title, episode title, and categories.
    - Filters compose seamlessly (`category`, `language`, `section`).
    - Only returns published content.
    """
    query = (
        select(Show)
        .where(Show.status == "published")
        .options(
            selectinload(Show.artworks),
            selectinload(Show.episodes).selectinload(Episode.artworks)
        )
    )

    if section:
        query = query.where(Show.section == section.lower())

    result = await db.execute(query)
    shows = result.scalars().all()

    filtered_results: List[SearchShowResult] = []
    q_lower = q.lower().strip() if q else None
    cat_lower = category.lower().strip() if category else None
    lang_lower = language.lower().strip() if language else None

    for show in shows:
        show_categories = [c.lower() for c in (show.categories or [])]

        # Category filter check
        if cat_lower and cat_lower not in show_categories:
            continue

        # Show artworks
        show_artworks = {a.slot_type: a.url for a in (show.artworks or [])}

        # Filter and match episodes
        matching_episodes = []
        show_title_matches = q_lower and (q_lower in show.title.lower() or q_lower in (show.synopsis or "").lower())
        show_category_matches = q_lower and any(q_lower in c for c in show_categories)

        for ep in show.episodes:
            if ep.status != "published":
                continue

            # Language filter check
            if lang_lower and ep.language.lower() != lang_lower:
                continue

            ep_title_matches = q_lower and (q_lower in ep.episode_title.lower() or q_lower in (ep.synopsis or "").lower())

            # If q is provided: episode matches if q in episode title, OR if q matches show title/category and episode satisfies language filter
            if not q_lower or ep_title_matches or show_title_matches or show_category_matches:
                matching_episodes.append({
                    "id": ep.id,
                    "episode_id": ep.episode_id,
                    "season_number": ep.season_number,
                    "episode_number": ep.episode_number,
                    "title": ep.episode_title,
                    "duration_seconds": ep.duration_seconds,
                    "language": ep.language,
                    "content_group": ep.content_group,
                    "synopsis": ep.synopsis,
                    "artwork": {
                        "thumbnail": next((a.url for a in (ep.artworks or []) if a.slot_type == "thumbnail"), show_artworks.get("thumbnail"))
                    }
                })

        # Include show if show matches search criteria and has matching episodes (or if no language filter restricted it)
        if matching_episodes or (not lang_lower and (show_title_matches or show_category_matches or not q_lower)):
            filtered_results.append(SearchShowResult(
                id=show.id,
                slug=show.slug,
                title=show.title,
                synopsis=show.synopsis,
                section=show.section,
                categories=show.categories or [],
                artwork=show_artworks,
                matching_episodes=matching_episodes
            ))

    return SearchResponse(
        total_matches=len(filtered_results),
        query=q,
        filters={
            "category": category,
            "language": language,
            "section": section
        },
        results=filtered_results
    )
