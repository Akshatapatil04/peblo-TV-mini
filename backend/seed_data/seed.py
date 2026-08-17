"""
Database seeder for Peblo TV Mini.
Loads seed_shows.json (95 episodes across 8 shows), creates show/season/episode models,
and generates corresponding artwork assets in storage.
"""
import os
import json
import asyncio
import io
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import AsyncSessionLocal, init_db
from backend.app.core.config import settings
from backend.app.models.show import Show
from backend.app.models.season import Season
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork
from backend.app.services.storage import get_storage

# Palette for show branding
SHOW_COLORS = {
    "motis-many-lives": (41, 128, 185),        # Deep Blue
    "tiny-tales-banyan-dadi": (39, 174, 96),   # Forest Green
    "discover-india-with-moti": (230, 126, 34), # Warm Orange
    "peblo-songs": (155, 89, 182),              # Purple
    "peblo-songs-lyrical": (142, 68, 173),      # Dark Purple
    "curious-cubs": (22, 160, 133),             # Teal
    "number-nest": (241, 196, 15),              # Yellow
    "rhyme-rangers": (231, 76, 60)              # Coral Red
}

def generate_artwork_bytes(slot_type: str, title: str, subtitle: str, bg_color: tuple) -> bytes:
    """Generate properly sized artwork bytes conforming to reference specs."""
    if slot_type == "poster":
        width, height = 600, 900
    elif slot_type == "banner":
        width, height = 1280, 720
    else:  # thumbnail
        width, height = 640, 360

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Decorative gradient-like borders
    draw.rectangle([(12, 12), (width - 12, height - 12)], outline=(255, 255, 255), width=3)
    
    # Text overlays
    draw.text((width // 8, height // 2 - 30), title[:24], fill=(255, 255, 255))
    draw.text((width // 8, height // 2 + 10), subtitle[:32], fill=(220, 220, 220))
    draw.text((width // 8, height // 2 + 40), f"{slot_type.upper()} ({width}x{height})", fill=(180, 180, 180))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()

async def seed_database(reset: bool = True):
    print("[INFO] Starting Peblo TV Mini database seed...")
    await init_db()
    storage = get_storage()

    seed_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "seed_shows.json"))
    with open(seed_file_path, "r", encoding="utf-8") as f:
        episodes_raw = json.load(f)

    async with AsyncSessionLocal() as db:
        if reset:
            print("[INFO] Cleaning existing data...")
            await db.execute(delete(Artwork))
            await db.execute(delete(Episode))
            await db.execute(delete(Season))
            await db.execute(delete(Show))
            await db.commit()

        # Group episodes by show slug
        shows_data = {}
        for row in episodes_raw:
            slug = row["slug"]
            if slug not in shows_data:
                shows_data[slug] = {
                    "slug": slug,
                    "title": row["show_title"],
                    "section": row["section"],
                    "categories": row["categories"],
                    "synopsis": row["synopsis"],
                    "status": "published" if row.get("section") and row.get("status") == "published" else row.get("status", "draft"),
                    "episodes": []
                }
            shows_data[slug]["episodes"].append(row)

        created_shows_count = 0
        created_episodes_count = 0
        created_artworks_count = 0

        for slug, s_data in shows_data.items():
            # Determine overall show status (if show has no section, it's draft)
            status = "published" if s_data["section"] is not None and any(e["status"] == "published" for e in s_data["episodes"]) else "draft"
            if slug == "rhyme-rangers":
                status = "draft"  # section is null

            show = Show(
                slug=slug,
                title=s_data["title"],
                section=s_data["section"],
                categories=s_data["categories"],
                synopsis=s_data["synopsis"],
                status=status
            )
            db.add(show)
            await db.flush()
            created_shows_count += 1

            bg_color = SHOW_COLORS.get(slug, (52, 73, 94))

            # 1. Create Show Artwork (Poster, Banner, Thumbnail)
            for slot_type in ["poster", "banner", "thumbnail"]:
                art_bytes = generate_artwork_bytes(slot_type, show.title, "Peblo TV Original", bg_color)
                w, h = (600, 900) if slot_type == "poster" else ((1280, 720) if slot_type == "banner" else (640, 360))
                file_key = f"uploads/{slot_type}/show_{slug}_{slot_type}.jpg"
                url = await storage.save(art_bytes, file_key, "image/jpeg")

                artwork = Artwork(
                    show_id=show.id,
                    slot_type=slot_type,
                    file_key=file_key,
                    url=url,
                    width=w,
                    height=h,
                    file_size_bytes=len(art_bytes),
                    mime_type="image/jpeg"
                )
                db.add(artwork)
                created_artworks_count += 1

            # 2. Organize Seasons
            seasons_map = {}
            for ep_row in s_data["episodes"]:
                s_num = ep_row["season_number"]
                if s_num not in seasons_map:
                    s_title = "Trailers" if s_num == 0 else f"Season {s_num}"
                    season = Season(
                        show_id=show.id,
                        season_number=s_num,
                        title=s_title
                    )
                    db.add(season)
                    await db.flush()
                    seasons_map[s_num] = season

            # 3. Create Episodes
            for ep_row in s_data["episodes"]:
                season = seasons_map[ep_row["season_number"]]
                episode = Episode(
                    episode_id=ep_row["episode_id"],
                    show_id=show.id,
                    season_id=season.id,
                    season_number=ep_row["season_number"],
                    episode_number=ep_row["episode_number"],
                    episode_title=ep_row["episode_title"],
                    duration_seconds=ep_row["duration_seconds"],
                    language=ep_row["language"],
                    content_group=ep_row["content_group"],
                    status=ep_row["status"],
                    synopsis=ep_row.get("synopsis") or show.synopsis
                )
                db.add(episode)
                await db.flush()
                created_episodes_count += 1

                # Generate Episode Artwork if listed in artwork_available
                # Note: If artwork_available is empty (like for ep_0036), no artwork is added!
                available_slots = ep_row.get("artwork_available", [])
                for slot_type in available_slots:
                    if slot_type in ("thumbnail", "poster", "banner"):
                        art_bytes = generate_artwork_bytes(
                            slot_type,
                            episode.episode_title,
                            f"{show.title} S{episode.season_number}E{episode.episode_number}",
                            bg_color
                        )
                        w, h = (640, 360) if slot_type == "thumbnail" else ((600, 900) if slot_type == "poster" else (1280, 720))
                        file_key = f"uploads/{slot_type}/ep_{ep_row['episode_id']}_{slot_type}.jpg"
                        url = await storage.save(art_bytes, file_key, "image/jpeg")

                        ep_artwork = Artwork(
                            episode_id=episode.id,
                            slot_type=slot_type,
                            file_key=file_key,
                            url=url,
                            width=w,
                            height=h,
                            file_size_bytes=len(art_bytes),
                            mime_type="image/jpeg"
                        )
                        db.add(ep_artwork)
                        created_artworks_count += 1

        await db.commit()
        print(f"[SUCCESS] Successfully seeded:")
        print(f"   * {created_shows_count} Shows")
        print(f"   * {len(shows_data)} Show Slugs")
        print(f"   * {created_episodes_count} Episodes")
        print(f"   * {created_artworks_count} Artwork Files")

if __name__ == "__main__":
    asyncio.run(seed_database(reset=True))
