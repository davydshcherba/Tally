from datetime import datetime, timedelta, timezone

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


async def test_create_link_with_custom_alias(client):
    resp = await client.post("/", json={"url": "https://example.com/page", "code": "my-alias"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == "my-alias"
    assert body["short_url"].endswith("my-alias")

    redirect_resp = await client.get("/my-alias")
    assert redirect_resp.status_code == 302


async def test_create_link_409_for_taken_alias(client):
    first_resp = await client.post("/", json={"url": "https://example.com/page", "code": "taken"})
    assert first_resp.status_code == 201

    second_resp = await client.post("/", json={"url": "https://example.com/other", "code": "taken"})
    assert second_resp.status_code == 409


async def test_create_link_409_for_reserved_alias(client):
    resp = await client.post("/", json={"url": "https://example.com/page", "code": "health"})
    assert resp.status_code == 409


async def test_create_link_422_for_invalid_alias_characters(client):
    resp = await client.post("/", json={"url": "https://example.com/page", "code": "not valid!"})
    assert resp.status_code == 422


async def test_create_link_rate_limited_per_ip(client):
    for _ in range(10):
        resp = await client.post("/", json={"url": "https://example.com/page"})
        assert resp.status_code == 201

    limited_resp = await client.post("/", json={"url": "https://example.com/page"})
    assert limited_resp.status_code == 429

    async with make_client("9.9.9.9") as other_ip_client:
        other_resp = await other_ip_client.post("/", json={"url": "https://example.com/page"})
        assert other_resp.status_code == 201


async def test_redirect_410_for_expired_link(client):
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    create_resp = await client.post("/", json={"url": "https://example.com/page", "expires_at": past})
    assert create_resp.status_code == 201
    code = create_resp.json()["code"]

    redirect_resp = await client.get(f"/{code}")
    assert redirect_resp.status_code == 410


async def test_redirect_succeeds_for_unexpired_link(client):
    future = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    create_resp = await client.post("/", json={"url": "https://example.com/page", "expires_at": future})
    assert create_resp.status_code == 201
    body = create_resp.json()
    code = body["code"]
    assert body["expires_at"] is not None

    redirect_resp = await client.get(f"/{code}")
    assert redirect_resp.status_code == 302


async def test_list_links_empty(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


async def test_list_links_pagination_newest_first(client):
    codes = []
    for i in range(3):
        create_resp = await client.post("/", json={"url": f"https://example.com/page{i}"})
        assert create_resp.status_code == 201
        codes.append(create_resp.json()["code"])

    first_page_resp = await client.get("/", params={"limit": 2, "offset": 0})
    assert first_page_resp.status_code == 200
    first_page = first_page_resp.json()
    assert first_page["total"] == 3
    assert first_page["limit"] == 2
    assert first_page["offset"] == 0
    assert len(first_page["items"]) == 2

    second_page_resp = await client.get("/", params={"limit": 2, "offset": 2})
    assert second_page_resp.status_code == 200
    second_page = second_page_resp.json()
    assert second_page["total"] == 3
    assert len(second_page["items"]) == 1

    listed_codes = [item["code"] for item in first_page["items"] + second_page["items"]]
    assert sorted(listed_codes) == sorted(codes)

    item = first_page["items"][0]
    assert item["short_url"].endswith(item["code"])
    assert item["original_url"].startswith("https://example.com/page")


async def test_list_links_rejects_invalid_pagination_params(client):
    assert (await client.get("/", params={"limit": 0})).status_code == 422
    assert (await client.get("/", params={"limit": 101})).status_code == 422
    assert (await client.get("/", params={"offset": -1})).status_code == 422


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
