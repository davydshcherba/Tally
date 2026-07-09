from tests.conftest import make_client


async def test_happy_path_create_redirect_stats_delete(client):
    create_resp = await client.post("/", json={"url": "https://example.com/page"})
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["original_url"] == "https://example.com/page"
    code = body["code"]
    assert body["short_url"].endswith(code)

    redirect_resp = await client.get(f"/{code}")
    assert redirect_resp.status_code == 302
    assert redirect_resp.headers["location"] == "https://example.com/page"

    stats_resp = await client.get(f"/{code}/stats")
    assert stats_resp.status_code == 200
    assert stats_resp.json() == {"code": code, "total_clicks": 1, "unique_clicks": 1}

    delete_resp = await client.delete(f"/{code}")
    assert delete_resp.status_code == 204

    missing_stats_resp = await client.get(f"/{code}/stats")
    assert missing_stats_resp.status_code == 404


async def test_redirect_404_for_unknown_code(client):
    resp = await client.get("/doesnotexist")
    assert resp.status_code == 404


async def test_stats_404_for_unknown_code(client):
    resp = await client.get("/doesnotexist/stats")
    assert resp.status_code == 404


async def test_delete_404_for_unknown_code(client):
    resp = await client.delete("/doesnotexist")
    assert resp.status_code == 404


async def test_create_link_422_for_invalid_url(client):
    resp = await client.post("/", json={"url": "not-a-url"})
    assert resp.status_code == 422


async def test_unique_vs_total_click_counting(client):
    create_resp = await client.post("/", json={"url": "https://example.com/page"})
    code = create_resp.json()["code"]

    async with make_client("1.2.3.4") as visitor_a:
        await visitor_a.get(f"/{code}")
        await visitor_a.get(f"/{code}")  # same visitor clicks twice

    async with make_client("5.6.7.8") as visitor_b:
        await visitor_b.get(f"/{code}")  # a different visitor clicks once

    stats_resp = await client.get(f"/{code}/stats")
    assert stats_resp.status_code == 200
    body = stats_resp.json()
    assert body["total_clicks"] == 3
    assert body["unique_clicks"] == 2
