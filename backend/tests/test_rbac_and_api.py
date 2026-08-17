import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.show import Show
from backend.app.models.season import Season
from backend.app.models.episode import Episode
from backend.app.models.artwork import Artwork

@pytest.mark.asyncio
async def test_editor_cannot_publish_catalog(client: AsyncClient):
    """Editor role must receive 403 Forbidden when calling publish endpoint."""
    response = await client.post(
        "/api/v1/admin/catalog/publish",
        headers={"X-User-Role": "editor"}
    )
    assert response.status_code == 403
    data = response.json()
    assert "Forbidden" in str(data)

@pytest.mark.asyncio
async def test_admin_can_call_publish_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Admin role can trigger publish endpoint."""
    # Create valid published show
    show = Show(slug="admin-test-show", title="Admin Test Show", section="songs", categories=["music"], status="published")
    db_session.add(show)
    await db_session.flush()

    art = Artwork(show_id=show.id, slot_type="poster", file_key="test.jpg", url="/test.jpg", width=600, height=900, file_size_bytes=10000)
    db_session.add(art)

    season = Season(show_id=show.id, season_number=1)
    db_session.add(season)
    await db_session.flush()

    ep = Episode(
        show_id=show.id,
        season_id=season.id,
        season_number=1,
        episode_number=1,
        episode_title="Song 1",
        duration_seconds=120,
        language="en",
        content_group="song-1-s01e01",
        status="published"
    )
    db_session.add(ep)
    await db_session.flush()
    art_ep = Artwork(episode_id=ep.id, slot_type="thumbnail", file_key="thumb.jpg", url="/thumb.jpg", width=640, height=360, file_size_bytes=10000)
    db_session.add(art_ep)
    await db_session.commit()

    response = await client.post(
        "/api/v1/admin/catalog/publish",
        headers={"X-User-Role": "admin"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["shows_count"] == 1

@pytest.mark.asyncio
async def test_composable_catalog_search(client: AsyncClient, db_session: AsyncSession):
    """Search endpoint filters must compose properly."""
    show1 = Show(slug="math-show", title="Math World", section="series", categories=["maths", "learning"], status="published")
    show2 = Show(slug="story-show", title="Folk Stories", section="series", categories=["stories", "folk"], status="published")
    db_session.add_all([show1, show2])
    await db_session.flush()

    season = Season(show_id=show1.id, season_number=1)
    db_session.add(season)
    await db_session.flush()

    ep1 = Episode(show_id=show1.id, season_id=season.id, season_number=1, episode_number=1, episode_title="Counting Stars", duration_seconds=300, language="en", content_group="math-01", status="published")
    ep2 = Episode(show_id=show1.id, season_id=season.id, season_number=1, episode_number=2, episode_title="Shapes Everywhere", duration_seconds=300, language="hi", content_group="math-02", status="published")
    db_session.add_all([ep1, ep2])
    await db_session.commit()

    # Search with q="Counting" -> matches Math World episode
    res1 = await client.get("/api/v1/catalog/search?q=Counting")
    assert res1.status_code == 200
    assert res1.json()["total_matches"] == 1
    assert res1.json()["results"][0]["slug"] == "math-show"

    # Search with category="maths" and language="hi" -> returns episode 2
    res2 = await client.get("/api/v1/catalog/search?category=maths&language=hi")
    assert res2.status_code == 200
    assert res2.json()["total_matches"] == 1
    assert len(res2.json()["results"][0]["matching_episodes"]) == 1
    assert res2.json()["results"][0]["matching_episodes"][0]["title"] == "Shapes Everywhere"

    # Search with category="folk" and section="songs" -> no match because section is series
    res3 = await client.get("/api/v1/catalog/search?category=folk&section=songs")
    assert res3.status_code == 200
    assert res3.json()["total_matches"] == 0

@pytest.mark.asyncio
async def test_validation_report_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Validation report returns structured blocking errors and remediation."""
    # Show missing section
    bad_show = Show(slug="no-section-show", title="No Section Show", section=None, categories=["nature"], status="published")
    db_session.add(bad_show)
    await db_session.commit()

    response = await client.get("/api/v1/admin/validation-report", headers={"X-User-Role": "editor"})
    assert response.status_code == 200
    data = response.json()
    assert data["can_publish"] is False
    assert data["total_blocking_errors"] >= 1
    err = next(e for e in data["blocking_errors"] if e["entity_id"] == bad_show.id)
    assert err["field"] == "section"
    assert "Assign one of the allowed sections" in err["remediation"]
