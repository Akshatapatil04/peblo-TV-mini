from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.show import Show
from backend.app.models.season import Season
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork
from backend.app.schemas.episode import (
    EpisodeCreate, EpisodeUpdate, EpisodeResponse, EpisodeListResponse
)
from backend.app.schemas.show import ArtworkInfo
from backend.app.api.deps import get_current_user, require_role
from backend.app.services.validation_report import ALLOWED_LANGUAGES

router = APIRouter(prefix="/episodes", tags=["Episodes"])

def _to_artwork_info(artwork: Artwork) -> ArtworkInfo:
    return ArtworkInfo(
        id=artwork.id,
        slot_type=artwork.slot_type,
        url=artwork.url,
        width=artwork.width,
        height=artwork.height,
        file_size_bytes=artwork.file_size_bytes
    )

def _to_episode_response(episode: Episode) -> EpisodeResponse:
    artworks = [_to_artwork_info(a) for a in (episode.artworks or [])]
    return EpisodeResponse(
        id=episode.id,
        episode_id=episode.episode_id,
        show_id=episode.show_id,
        season_id=episode.season_id,
        season_number=episode.season_number,
        episode_number=episode.episode_number,
        episode_title=episode.episode_title,
        duration_seconds=episode.duration_seconds,
        language=episode.language,
        content_group=episode.content_group,
        status=episode.status,
        synopsis=episode.synopsis,
        created_at=episode.created_at,
        updated_at=episode.updated_at,
        artworks=artworks,
        show_title=episode.show.title if episode.show else None,
        show_slug=episode.show.slug if episode.show else None
    )

@router.get("", response_model=EpisodeListResponse)
async def list_episodes(
    db: AsyncSession = Depends(get_db),
    show_id: Optional[str] = None,
    season_number: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    language: Optional[str] = None,
    content_group: Optional[str] = None,
    section: Optional[str] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """List episodes with rich filtering by show, season, status, language, content_group, section, and search query."""
    query = (
        select(Episode)
        .join(Show, Episode.show_id == Show.id)
        .options(
            selectinload(Episode.artworks),
            selectinload(Episode.show)
        )
    )

    if show_id:
        query = query.where(or_(Episode.show_id == show_id, Show.slug == show_id))
    if season_number is not None:
        query = query.where(Episode.season_number == season_number)
    if status_filter and status_filter.lower() != "all":
        query = query.where(Episode.status == status_filter.lower())
    if language:
        query = query.where(Episode.language == language.lower())
    if content_group:
        query = query.where(Episode.content_group == content_group)
    if section:
        query = query.where(Show.section == section)
    if q:
        query = query.where(or_(
            Episode.episode_title.ilike(f"%{q}%"),
            Episode.content_group.ilike(f"%{q}%"),
            Episode.episode_id.ilike(f"%{q}%"),
            Show.title.ilike(f"%{q}%")
        ))

    # Count total
    count_query = select(func.count(Episode.id)).join(Show, Episode.show_id == Show.id)
    if show_id:
        count_query = count_query.where(or_(Episode.show_id == show_id, Show.slug == show_id))
    if season_number is not None:
        count_query = count_query.where(Episode.season_number == season_number)
    if status_filter and status_filter.lower() != "all":
        count_query = count_query.where(Episode.status == status_filter.lower())
    if language:
        count_query = count_query.where(Episode.language == language.lower())
    if content_group:
        count_query = count_query.where(Episode.content_group == content_group)
    if section:
        count_query = count_query.where(Show.section == section)
    if q:
        count_query = count_query.where(or_(
            Episode.episode_title.ilike(f"%{q}%"),
            Episode.content_group.ilike(f"%{q}%"),
            Episode.episode_id.ilike(f"%{q}%"),
            Show.title.ilike(f"%{q}%")
        ))

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    query = query.order_by(Show.title, Episode.season_number, Episode.episode_number).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    episodes = result.scalars().all()

    items = [_to_episode_response(e) for e in episodes]
    return EpisodeListResponse(total=total, items=items)

@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve an episode by its database ID or external episode_id (e.g. ep_0001)."""
    query = (
        select(Episode)
        .where(or_(Episode.id == episode_id, Episode.episode_id == episode_id))
        .options(
            selectinload(Episode.artworks),
            selectinload(Episode.show)
        )
    )
    result = await db.execute(query)
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Episode '{episode_id}' not found.")
    return _to_episode_response(episode)

@router.post("", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
async def create_episode(
    payload: EpisodeCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """Create a new episode with strict validation rules."""
    # Verify show exists
    show_res = await db.execute(select(Show).where(Show.id == payload.show_id))
    show = show_res.scalar_one_or_none()
    if not show:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Show with id '{payload.show_id}' not found.")

    # 1. Uniqueness check for (content_group, language)
    dup_res = await db.execute(
        select(Episode).where(
            Episode.content_group == payload.content_group,
            Episode.language == payload.language
        )
    )
    if dup_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An episode with content_group '{payload.content_group}' and language '{payload.language}' already exists."
        )

    # 2. Validate language
    if payload.language not in ALLOWED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language '{payload.language}'. Allowed languages: {', '.join(sorted(ALLOWED_LANGUAGES))}."
        )

    # 3. Resolve or create season
    season_id = payload.season_id
    if not season_id:
        season_res = await db.execute(
            select(Season).where(Season.show_id == payload.show_id, Season.season_number == payload.season_number)
        )
        season = season_res.scalar_one_or_none()
        if not season:
            season_title = "Trailers" if payload.season_number == 0 else f"Season {payload.season_number}"
            season = Season(show_id=payload.show_id, season_number=payload.season_number, title=season_title)
            db.add(season)
            await db.flush()
        season_id = season.id

    # 4. Check publish requirements
    if payload.status == "published":
        if payload.duration_seconds <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An episode cannot be published without a positive duration in seconds."
            )

    episode = Episode(
        episode_id=payload.episode_id,
        show_id=payload.show_id,
        season_id=season_id,
        season_number=payload.season_number,
        episode_number=payload.episode_number,
        episode_title=payload.episode_title,
        duration_seconds=payload.duration_seconds,
        language=payload.language,
        content_group=payload.content_group,
        status=payload.status,
        synopsis=payload.synopsis
    )
    db.add(episode)
    await db.commit()
    await db.refresh(episode)
    
    # Reload with relations
    return await get_episode(episode.id, db)

@router.put("/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: str,
    payload: EpisodeUpdate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """Update an episode."""
    query = select(Episode).where(or_(Episode.id == episode_id, Episode.episode_id == episode_id)).options(selectinload(Episode.artworks), selectinload(Episode.show))
    result = await db.execute(query)
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Episode '{episode_id}' not found.")

    target_content_group = payload.content_group or episode.content_group
    target_language = payload.language or episode.language

    # Check (content_group, language) uniqueness if either changed
    if (target_content_group != episode.content_group) or (target_language != episode.language):
        dup_res = await db.execute(
            select(Episode).where(
                Episode.content_group == target_content_group,
                Episode.language == target_language,
                Episode.id != episode.id
            )
        )
        if dup_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An episode with content_group '{target_content_group}' and language '{target_language}' already exists."
            )

    if payload.language is not None:
        if payload.language not in ALLOWED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid language '{payload.language}'. Allowed: {', '.join(sorted(ALLOWED_LANGUAGES))}."
            )
        episode.language = payload.language

    if payload.episode_title is not None:
        episode.episode_title = payload.episode_title
    if payload.content_group is not None:
        episode.content_group = payload.content_group
    if payload.duration_seconds is not None:
        episode.duration_seconds = payload.duration_seconds
    if payload.episode_number is not None:
        episode.episode_number = payload.episode_number
    if payload.synopsis is not None:
        episode.synopsis = payload.synopsis
    if payload.status is not None:
        if payload.status == "published":
            if episode.duration_seconds <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An episode cannot be published without a positive duration in seconds."
                )
            if not episode.artworks and not (episode.show and episode.show.artworks):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An episode cannot be published without artwork."
                )
        episode.status = payload.status

    await db.commit()
    await db.refresh(episode)
    return await get_episode(episode.id, db)

@router.delete("/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """Delete an episode."""
    query = select(Episode).where(or_(Episode.id == episode_id, Episode.episode_id == episode_id))
    result = await db.execute(query)
    episode = result.scalar_one_or_none()
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Episode '{episode_id}' not found.")

    await db.delete(episode)
    await db.commit()
    return None
