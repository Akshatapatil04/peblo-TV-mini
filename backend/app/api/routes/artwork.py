import uuid
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.show import Show
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork
from backend.app.schemas.artwork import ArtworkUploadResponse
from backend.app.services.image_validator import validate_artwork, ImageValidationError
from backend.app.services.storage import get_storage
from backend.app.api.deps import require_role

router = APIRouter(prefix="/artwork", tags=["Artwork"])

@router.post("/upload", response_model=ArtworkUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_artwork(
    file: UploadFile = File(...),
    slot_type: str = Form(..., description="poster (2:3), banner (16:9), or thumbnail (16:9)"),
    show_id: Optional[str] = Form(None),
    episode_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """
    Upload and validate artwork for a Show or Episode.
    Strictly validates:
    - 200 KB maximum file size limit
    - 2:3 aspect ratio (~600x900) for poster
    - 16:9 aspect ratio (~1280x720) for banner
    - 16:9 aspect ratio (~640x360) for thumbnail
    - Valid JPEG / PNG / WebP format
    Returns human-friendly, actionable error messages upon failure.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    # 1. Validate Image Specs
    try:
        image, meta = validate_artwork(file_bytes=file_bytes, slot_type=slot_type)
    except ImageValidationError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Image validation failed",
                "message": err.message,
                "details": err.details
            }
        )

    # 2. Resolve Target Show / Episode if provided
    db_show_id = None
    db_episode_id = None

    if show_id:
        show_res = await db.execute(select(Show).where(or_(Show.id == show_id, Show.slug == show_id)))
        show = show_res.scalar_one_or_none()
        if not show:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Show '{show_id}' not found.")
        db_show_id = show.id

    if episode_id:
        ep_res = await db.execute(select(Episode).where(or_(Episode.id == episode_id, Episode.episode_id == episode_id)))
        episode = ep_res.scalar_one_or_none()
        if not episode:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Episode '{episode_id}' not found.")
        db_episode_id = episode.id

    # 3. Store via Storage Abstraction
    ext = meta["format"].lower()
    if ext == "jpeg":
        ext = "jpg"
    unique_name = f"{uuid.uuid4().hex[:12]}_{slot_type}.{ext}"
    storage_key = f"uploads/{slot_type}/{unique_name}"
    
    storage = get_storage()
    url = await storage.save(file_bytes, storage_key, content_type=meta["mime_type"])

    # 4. If replacing existing slot on entity, delete old record
    if db_show_id:
        old_art_res = await db.execute(
            select(Artwork).where(Artwork.show_id == db_show_id, Artwork.slot_type == slot_type)
        )
        for old_art in old_art_res.scalars().all():
            await storage.delete(old_art.file_key)
            await db.delete(old_art)

    if db_episode_id:
        old_art_res = await db.execute(
            select(Artwork).where(Artwork.episode_id == db_episode_id, Artwork.slot_type == slot_type)
        )
        for old_art in old_art_res.scalars().all():
            await storage.delete(old_art.file_key)
            await db.delete(old_art)

    # 5. Create new Artwork DB record
    artwork = Artwork(
        show_id=db_show_id,
        episode_id=db_episode_id,
        slot_type=slot_type,
        file_key=storage_key,
        url=url,
        width=meta["width"],
        height=meta["height"],
        file_size_bytes=meta["file_size_bytes"],
        mime_type=meta["mime_type"]
    )
    db.add(artwork)
    await db.commit()
    await db.refresh(artwork)

    return ArtworkUploadResponse(
        id=artwork.id,
        slot_type=artwork.slot_type,
        url=artwork.url,
        width=artwork.width,
        height=artwork.height,
        file_size_bytes=artwork.file_size_bytes,
        file_size_kb=meta["file_size_kb"],
        mime_type=artwork.mime_type,
        aspect_ratio=meta["aspect_ratio"],
        show_id=artwork.show_id,
        episode_id=artwork.episode_id,
        created_at=artwork.created_at
    )

@router.delete("/{artwork_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artwork(
    artwork_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role(["admin", "editor"]))
):
    """Delete an artwork record and its storage file."""
    result = await db.execute(select(Artwork).where(Artwork.id == artwork_id))
    artwork = result.scalar_one_or_none()
    if not artwork:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artwork '{artwork_id}' not found.")

    storage = get_storage()
    await storage.delete(artwork.file_key)
    await db.delete(artwork)
    await db.commit()
    return None
