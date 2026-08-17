import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.show import Show
from backend.app.models.season import Season
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork
from backend.app.models.publish_run import PublishRun
from backend.app.services.publisher import execute_publish
from backend.app.services.storage import get_storage

@pytest.mark.asyncio
async def test_publish_collapses_language_variants(db_session: AsyncSession):
    """Verify that multiple episodes with the same content_group collapse into 1 catalogue entry."""
    # 1. Create Show
    show = Show(
        slug="test-show",
        title="Test Show",
        section="featured",
        categories=["adventure", "india"],
        status="published"
    )
    db_session.add(show)
    await db_session.flush()

    # Show poster & banner
    art_poster = Artwork(show_id=show.id, slot_type="poster", file_key="uploads/poster/test.jpg", url="/test_poster.jpg", width=600, height=900, file_size_bytes=20000)
    art_banner = Artwork(show_id=show.id, slot_type="banner", file_key="uploads/banner/test.jpg", url="/test_banner.jpg", width=1280, height=720, file_size_bytes=30000)
    db_session.add_all([art_poster, art_banner])

    # 2. Create Season 1
    season1 = Season(show_id=show.id, season_number=1, title="Season 1")
    db_session.add(season1)
    await db_session.flush()

    # 3. Create 2 language variants for episode 1 (English and Hindi)
    ep_en = Episode(
        episode_id="ep_test_en",
        show_id=show.id,
        season_id=season1.id,
        season_number=1,
        episode_number=1,
        episode_title="The Lost Kite (English)",
        duration_seconds=500,
        language="en",
        content_group="test-show-s01e01",
        status="published"
    )
    ep_hi = Episode(
        episode_id="ep_test_hi",
        show_id=show.id,
        season_id=season1.id,
        season_number=1,
        episode_number=1,
        episode_title="The Lost Kite (Hindi)",
        duration_seconds=490,
        language="hi",
        content_group="test-show-s01e01",
        status="published"
    )
    db_session.add_all([ep_en, ep_hi])
    await db_session.flush()

    # Episode artworks
    art_ep_en = Artwork(episode_id=ep_en.id, slot_type="thumbnail", file_key="uploads/thumbnail/en.jpg", url="/en_thumb.jpg", width=640, height=360, file_size_bytes=10000)
    art_ep_hi = Artwork(episode_id=ep_hi.id, slot_type="thumbnail", file_key="uploads/thumbnail/hi.jpg", url="/hi_thumb.jpg", width=640, height=360, file_size_bytes=10000)
    db_session.add_all([art_ep_en, art_ep_hi])

    # 4. Create Season 0 Trailer
    season0 = Season(show_id=show.id, season_number=0, title="Trailers")
    db_session.add(season0)
    await db_session.flush()

    ep_trailer = Episode(
        episode_id="ep_trailer_01",
        show_id=show.id,
        season_id=season0.id,
        season_number=0,
        episode_number=1,
        episode_title="Show Trailer",
        duration_seconds=60,
        language="en",
        content_group="test-show-s00e01",
        status="published"
    )
    db_session.add(ep_trailer)
    await db_session.flush()
    art_trailer = Artwork(episode_id=ep_trailer.id, slot_type="thumbnail", file_key="uploads/thumbnail/tr.jpg", url="/tr_thumb.jpg", width=640, height=360, file_size_bytes=10000)
    db_session.add(art_trailer)

    await db_session.commit()

    # 5. Execute Publish
    result = await execute_publish(db_session, initiated_by="test_admin@peblo.tv")
    assert result["status"] == "success"
    assert result["shows_count"] == 1
    assert result["episodes_count"] == 2  # 1 collapsed main episode + 1 trailer

    # 6. Verify catalogue contents from storage
    storage = get_storage()
    cat_bytes = await storage.get("catalog/catalogue.json")
    import json
    catalogue = json.loads(cat_bytes.decode("utf-8"))

    # Check sections
    featured_sec = next(s for s in catalogue["sections"] if s["section_id"] == "featured")
    assert len(featured_sec["shows"]) == 1
    published_show = featured_sec["shows"][0]

    # Verify Season 0 trailers are separated from regular seasons
    assert len(published_show["trailers"]) == 1
    assert published_show["trailers"][0]["content_group"] == "test-show-s00e01"
    assert len(published_show["seasons"]) == 1

    # Verify collapsed episode in Season 1
    s1_episodes = published_show["seasons"][0]["episodes"]
    assert len(s1_episodes) == 1  # 2 variants collapsed into 1!
    collapsed_ep = s1_episodes[0]
    assert collapsed_ep["content_group"] == "test-show-s01e01"
    assert sorted(collapsed_ep["languages"]) == ["en", "hi"]
    assert len(collapsed_ep["audio_variants"]) == 2

@pytest.mark.asyncio
async def test_publish_blocked_by_missing_duration(db_session: AsyncSession):
    """Publish must be blocked if an episode is published with 0 duration."""
    show = Show(slug="broken-show", title="Broken Show", section="series", categories=["learning"], status="published")
    db_session.add(show)
    await db_session.flush()

    art_poster = Artwork(show_id=show.id, slot_type="poster", file_key="test.jpg", url="/test.jpg", width=600, height=900, file_size_bytes=20000)
    db_session.add(art_poster)

    season1 = Season(show_id=show.id, season_number=1)
    db_session.add(season1)
    await db_session.flush()

    # Episode with 0 duration
    ep = Episode(
        show_id=show.id,
        season_id=season1.id,
        season_number=1,
        episode_number=1,
        episode_title="Zero Duration",
        duration_seconds=0,
        language="en",
        content_group="broken-s01e01",
        status="published"
    )
    db_session.add(ep)
    await db_session.commit()

    from backend.app.services.publisher import PublishError
    with pytest.raises(PublishError):
        await execute_publish(db_session)
