from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.show import Show
from backend.app.models.season import Season
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork
from backend.app.schemas.show import (
    ShowCreate, ShowUpdate, ShowResponse, ShowDetailResponse, ShowListResponse,
    ArtworkInfo, EpisodeSummary, SeasonResponse
)
from backend.app.api.deps import get_current_user, require_role
from backend.app.services.validation_report import ALLOWED_SECTIONS, ALLOWED_CATEGORIES

router = APIRouter(prefix="/shows", tags=["Shows"])

def _to_artwork_info(artwork: Artwork) -> ArtworkInfo:
    return ArtworkInfo(
        id=artwork.id,
        slot_type=artwork.slot_type,
        url=artwork.url,
        width=artwork.width,
        height=artwork.height,
        file_size_bytes=artwork.file_size_bytes
    )

def _to_show_response(show: Show, seasons_count: int = 0, episodes_count: int = 0) -> ShowResponse:
    artworks = [_to_artwork_info(a) for a in (show.artworks or [])]
    return ShowResponse(
        id=show.id,
        slug=show.slug,
        title=show.title,
        synopsis=show.synopsis,
        section=show.section,
        categories=show.categories or [],
        status=show.status,
        created_at=show.created_at,
        updated_at=show.updated_at,
        artworks=artworks,
        seasons_count=seasons_count,
        episodes_count=episodes_count
    )

@router.get("", response_model=ShowListResponse)
async def list_shows(
    db: AsyncSession = Depends(get_db),
    section: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """List shows with filtering by section, status, category, title search, and pagination."""
    query = (
        select(Show)
        .options(
            selectinload(Show.artworks),
            selectinload(Show.seasons),
            selectinload(Show.episodes)
        )
    )

    if section:
        query = query.where(Show.section == section)
    if status_filter and status_filter.lower() != "all":
        query = query.where(Show.status == status_filter.lower())
    if q:
        query = query.where(or_(
            Show.title.ilike(f"%{q}%"),
            Show.synopsis.ilike(f"%{q}%"),
            Show.slug.ilike(f"%{q}%")
        ))

    # Total count
    count_query = select(func.count(Show.id))
    if section:
        count_query = count_query.where(Show.section == section)
    if status_filter and status_filter.lower() != "all":
        count_query = count_query.where(Show.status == status_filter.lower())
    if q:
        count_query = count_query.where(or_(
            Show.title.ilike(f"%{q}%"),
            Show.synopsis.ilike(f"%{q}%"),
            Show.slug.ilike(f"%{q}%")
        ))
    
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    # Paginate and order by title
    query = query.order_by(Show.title).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    shows = result.scalars().all()

    items = []
    for s in shows:
        # If category filter requested, filter in-memory if array JSON
        if category and category not in (s.categories or []):
            continue
        items.append(_to_show_response(s, len(s.seasons), len(s.episodes)))

    return ShowListResponse(total=total, items=items)

@router.get("/{show_id_or_slug}", response_model=ShowDetailResponse)
async def get_show_detail(
    show_id_or_slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve full show details with seasons, episodes, and artwork."""
    query = (
        select(Show)
        .where(or_(Show.id == show_id_or_slug, Show.slug == show_id_or_slug))
        .options(
            selectinload(Show.artworks),
            selectinload(Show.seasons).selectinload(Season.episodes).selectinload(Episode.artworks),
            selectinload(Show.episodes).selectinload(Episode.artworks)
        )
    )
    result = await db.execute(query)
    show = result.scalar_one_or_none()

    if not show:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Show '{show_id_or_slug}' not found.")

    artworks = [_to_artwork_info(a) for a in (show.artworks or [])]

    # Format seasons and episodes
    seasons_data = []
    # Sort seasons: Season 0 first, then 1, 2...
    sorted_seasons = sorted(show.seasons, key=lambda s: s.season_number)

    for s in sorted_seasons:
        sorted_episodes = sorted(s.episodes, key=lambda e: e.episode_number)
        episodes_data = [
            EpisodeSummary(
                id=ep.id,
                episode_id=ep.episode_id,
                season_number=ep.season_number,
                episode_number=ep.episode_number,
                episode_title=ep.episode_title,
                duration_seconds=ep.duration_seconds,
                language=ep.language,
                content_group=ep.content_group,
                status=ep.status,
                synopsis=ep.synopsis,
                artworks=[_to_artwork_info(a) for a in (ep.artworks or [])]
            )
            for ep in sorted_episodes
        ]
        seasons_data.append(SeasonResponse(
            id=s.id,
            show_id=s.show_id,
            season_number=s.season_number,
            title=s.title or (f"Trailers" if s.season_number == 0 else f"Season {s.season_number}"),
            episodes=episodes_data
        ))

    return ShowDetailResponse(
        id=show.id,
        slug=show.slug,
        title=show.title,
        synopsis=show.synopsis,
        section=show.section,
        categories=show.categories or [],
        status=show.status,
        created_at=show.created_at,
        updated_at=show.updated_at,
        artworks=artworks,
        seasons_count=len(show.seasons),
        episodes_count=len(show.episodes),
        seasons=seasons_data
    )

@router.post("", response_model=ShowResponse, status_code=status.HTTP_201_CREATED)
async def create_show(
    payload: ShowCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """Create a new show."""
    # Check slug uniqueness
    existing_slug = await db.execute(select(Show).where(Show.slug == payload.slug))
    if existing_slug.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Show slug '{payload.slug}' already exists.")

    # Validate section if provided
    if payload.section and payload.section not in ALLOWED_SECTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid section '{payload.section}'. Allowed sections: {', '.join(sorted(ALLOWED_SECTIONS))}."
        )

    # Validate published requirements
    if payload.status == "published" and not payload.section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A published show must have a section assigned."
        )

    show = Show(
        title=payload.title,
        slug=payload.slug,
        synopsis=payload.synopsis,
        section=payload.section,
        categories=payload.categories,
        status=payload.status
    )
    db.add(show)
    await db.commit()
    await db.refresh(show)
    return _to_show_response(show)

@router.put("/{show_id}", response_model=ShowResponse)
async def update_show(
    show_id: str,
    payload: ShowUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """Update show metadata, categories, section, or publish status."""
    result = await db.execute(
        select(Show).where(Show.id == show_id).options(selectinload(Show.artworks), selectinload(Show.seasons), selectinload(Show.episodes))
    )
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Show with id '{show_id}' not found.")

    if payload.slug is not None and payload.slug != show.slug:
        existing = await db.execute(select(Show).where(Show.slug == payload.slug))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Show slug '{payload.slug}' already in use.")
        show.slug = payload.slug

    if payload.title is not None:
        show.title = payload.title
    if payload.synopsis is not None:
        show.synopsis = payload.synopsis
    if payload.section is not None:
        if payload.section and payload.section not in ALLOWED_SECTIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid section '{payload.section}'. Allowed sections: {', '.join(sorted(ALLOWED_SECTIONS))}."
            )
        show.section = payload.section
    if payload.categories is not None:
        show.categories = payload.categories
    if payload.status is not None:
        if payload.status == "published" and not show.section:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A published show must have a section assigned."
            )
        show.status = payload.status

    await db.commit()
    await db.refresh(show)
    return _to_show_response(show, len(show.seasons), len(show.episodes))

@router.delete("/{show_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_show(
    show_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin"]))
):
    """Delete a show and its associated seasons and episodes (Admin only)."""
    result = await db.execute(select(Show).where(Show.id == show_id))
    show = result.scalar_one_or_none()
    if not show:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Show with id '{show_id}' not found.")

    await db.delete(show)
    await db.commit()
    return None
