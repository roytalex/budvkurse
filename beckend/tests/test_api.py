import asyncio
from datetime import datetime, timedelta
from io import BytesIO
import pytest
from PIL import Image
from sqlalchemy import select
from db.models import UserSession
from .helpers import PREFIX as P, account, event_setup


async def test_auth_rotation_logout_and_deactivation(api):
    client = api[0]
    headers, user, tokens = await account(api)
    assert "password_hash" not in user
    assert (await client.get(f"{P}/me", headers=headers)).status_code == 200
    assert (await client.patch(f"{P}/me", headers=headers, json={"role": "admin"})).status_code == 422
    assert (await client.patch(f"{P}/me", headers=headers, json={"name": None})).status_code == 422
    assert (await client.post(f"{P}/auth/login", json={"email": user["email"], "password": "wrong"})).status_code == 401
    renewed = await client.post(f"{P}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert renewed.status_code == 200, renewed.text
    assert (await client.post(f"{P}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})).status_code == 401
    assert (await client.get(f"{P}/me", headers=headers)).status_code == 401
    fresh = {"Authorization": f"Bearer {renewed.json()['access_token']}"}
    async with api[1]() as db:
        sessions = (await db.scalars(select(UserSession))).all()
        assert all(s.refresh_token_hash != tokens["refresh_token"] for s in sessions)
    assert (await client.delete(f"{P}/me", headers=fresh)).status_code == 204
    assert (await client.get(f"{P}/me", headers=fresh)).status_code == 401
    assert (await client.post(f"{P}/auth/refresh", json={"refresh_token": renewed.json()["refresh_token"]})).status_code == 401


async def test_publication_permissions_and_patch_validation(api):
    client = api[0]
    admin, owner, eid, body = await event_setup(api, published=False)
    other, _, _ = await account(api, "other", "organizer")
    student, _, _ = await account(api)
    assert (await client.get(f"{P}/events/{eid}", headers=student)).status_code == 404

    assert (await client.post(f"{P}/events/{eid}/cancel", headers=owner)).status_code == 409
    assert (await client.patch(f"{P}/events/{eid}", headers=other, json={"title": "Чужое"})).status_code == 403
    assert (await client.post(f"{P}/events", headers=student, json=body)).status_code == 403
    assert (await client.patch(f"{P}/events/{eid}", headers=owner, json={"ends_at": body["starts_at"]})).status_code == 422
    assert (await client.patch(f"{P}/events/{eid}", headers=owner, json={"latitude": None})).status_code == 422
    assert (await client.patch(f"{P}/events/{eid}", headers=owner, json={"status": "published"})).status_code == 422
    assert (await client.post(f"{P}/events/{eid}/submit", headers=owner)).status_code == 200
    assert (await client.post(f"{P}/events/{eid}/publish", headers=other)).status_code == 403
    assert (await client.post(f"{P}/events/{eid}/reject", headers=admin, json={"comment": "Уточните описание"})).status_code == 200
    assert (await client.post(f"{P}/events/{eid}/submit", headers=owner)).status_code == 200
    assert (await client.post(f"{P}/events/{eid}/publish", headers=admin)).status_code == 200
    assert (await client.get(f"{P}/events/{eid}", headers=student)).status_code == 200
    history = await client.get(f"{P}/events/{eid}/moderation", headers=owner)
    assert len(history.json()) == 2
    assert (await client.delete(f"{P}/events/{eid}", headers=owner)).status_code == 409
    changed = await client.patch(f"{P}/events/{eid}", headers=owner, json={"title": "Новое название"})
    assert changed.json()["status"] == "published"


async def test_filters_map_calendar_favorites_plans(api):
    client = api[0]
    admin, owner, eid, body = await event_setup(api)
    user, _, _ = await account(api)
    middle = datetime.fromisoformat(body["starts_at"]) + timedelta(days=1)
    response = await client.get(f"{P}/events", headers=user, params={"date_from": middle.isoformat(), "date_to": (middle+timedelta(hours=1)).isoformat(), "search": "школьников"})
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    bounds = dict(west=37, south=55, east=38, north=56)
    assert (await client.get(f"{P}/events/map", headers=user, params=bounds)).json()["total"] == 1
    assert (await client.get(f"{P}/events/map", headers=user, params=dict(west=170, south=-90, east=-170, north=90))).json()["total"] == 0
    assert (await client.get(f"{P}/events/map", headers=user, params=dict(west=0, south=90, east=1, north=-90))).status_code == 422
    for _ in range(2):
        assert (await client.put(f"{P}/me/favorites/{eid}", headers=user)).status_code == 200
        assert (await client.put(f"{P}/me/plans/{eid}", headers=user, json={"reminder_minutes_before": 60})).status_code == 200
    assert (await client.get(f"{P}/me/favorites", headers=user)).json()["total"] == 1
    assert (await client.get(f"{P}/me/plans", headers=user)).json()["total"] == 1
    card = (await client.get(f"{P}/events", headers=user)).json()["items"][0]
    assert card["is_favorite"] and card["in_plans"]
    assert (await client.delete(f"{P}/me/plans/{eid}", headers=user)).status_code == 204
    assert (await client.post(f"{P}/events/{eid}/cancel", headers=owner)).status_code == 200
    assert (await client.get(f"{P}/events/{eid}", headers=user)).json()["status"] == "cancelled"
    assert (await client.get(f"{P}/events", headers=user)).json()["total"] == 0
    assert (await client.post(f"{P}/events/{eid}/registrations", headers=user)).status_code == 409


async def test_registration_capacity_and_cancel_while_pending(api):
    client = api[0]
    admin, owner, eid, _ = await event_setup(api)
    first, _, _ = await account(api, "first")
    second, _, _ = await account(api, "second")
    url = f"{P}/events/{eid}/registrations"
    assert (await client.post(url, headers=first)).status_code == 201
    assert (await client.post(url, headers=first)).status_code == 409
    assert (await client.post(url, headers=second)).status_code == 409
    assert (await client.get(url, headers=second)).status_code == 403
    assert (await client.delete(url+"/me", headers=first)).status_code == 204
    assert (await client.post(url, headers=second)).status_code == 201
    assert (await client.patch(f"{P}/events/{eid}", headers=owner, json={"title": "Уточнённый хакатон"})).status_code == 200
    assert (await client.delete(url+"/me", headers=second)).status_code == 204


async def test_last_place_concurrency_postgresql(api):
    if api[2].dialect.name != "postgresql":
        pytest.skip("Блокировки FOR UPDATE проверяются в PostgreSQL")
    _, _, eid, _ = await event_setup(api)
    first, _, _ = await account(api, "first")
    second, _, _ = await account(api, "second")
    results = await asyncio.gather(*(api[0].post(f"{P}/events/{eid}/registrations", headers=h) for h in (first, second)))
    assert sorted(r.status_code for r in results) == [201, 409]


async def test_school_city_links_interests_and_transaction(api):
    client = api[0]
    admin, owner, eid, body = await event_setup(api, published=False)
    user, _, _ = await account(api)
    school = await client.post(f"{P}/schools", headers=admin, json=dict(city_id=body["city_id"], name="Школа 1", address="Улица 1"))
    assert school.status_code == 201, school.text
    sid = school.json()["id"]
    assert (await client.patch(f"{P}/me", headers=user, json={"school_id": sid})).status_code == 422
    assert (await client.patch(f"{P}/me", headers=user, json={"school_id": sid, "city_id": body["city_id"]})).status_code == 200
    assert (await client.delete(f"{P}/cities/{body['city_id']}", headers=admin)).status_code == 409
    topic = await client.post(f"{P}/topics", headers=admin, json={"name": "IT", "slug": "it"})
    tid = topic.json()["id"]
    assert (await client.put(f"{P}/me/interests", headers=user, json={"topic_ids": [tid]})).status_code == 200
    assert (await client.put(f"{P}/me/interests", headers=user, json={"topic_ids": [999999]})).status_code == 422
    assert (await client.get(f"{P}/me/interests", headers=user)).json()[0]["id"] == tid
    assert (await client.delete(f"{P}/topics/{tid}", headers=admin)).status_code == 409
    assert (await client.delete(f"{P}/schools/{sid}", headers=admin)).status_code == 204


async def test_file_validation_private_access_and_deletion(api):
    client = api[0]
    owner, _, _ = await account(api, "owner", "organizer")
    other, _, _ = await account(api, "other", "organizer")
    invalid = await client.post(f"{P}/files", headers=owner, files={"file": ("bad.png", b"not an image", "image/png")})
    assert invalid.status_code == 422, invalid.text
    output = BytesIO()
    Image.new("RGB", (10, 10)).save(output, format="PNG")
    uploaded = await client.post(f"{P}/files", headers=owner, files={"file": ("test.png", output.getvalue(), "image/png")})
    assert uploaded.status_code == 201, uploaded.text
    fid, url = uploaded.json()["id"], uploaded.json()["url"]
    assert (await client.get(url)).status_code == 401
    assert (await client.get(url, headers=owner)).content == output.getvalue()
    assert (await client.delete(f"{P}/files/{fid}", headers=other)).status_code == 403
    assert (await client.delete(f"{P}/files/{fid}", headers=owner)).status_code == 204
    assert (await client.get(url, headers=owner)).status_code == 404


async def test_refresh_concurrency_and_logout_postgresql(api):
    if api[2].dialect.name != "postgresql":
        pytest.skip("Блокировки refresh проверяются в PostgreSQL")
    client = api[0]
    _, _, tokens = await account(api)
    results = await asyncio.gather(*(client.post(f"{P}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}) for _ in range(2)))
    assert sorted(r.status_code for r in results) == [200, 401]
    fresh = next(r.json() for r in results if r.status_code == 200)
    assert (await client.post(f"{P}/auth/logout", json={"refresh_token": fresh["refresh_token"]})).status_code == 204
    assert (await client.get(f"{P}/me", headers={"Authorization": f"Bearer {fresh['access_token']}"})).status_code == 401


async def test_registration_grade_and_deadline(api):
    client = api[0]
    admin, owner, eid, body = await event_setup(api, published=False)
    user, _, _ = await account(api)
    assert (await client.patch(f"{P}/events/{eid}", headers=owner, json={"min_grade": 9, "max_grade": 11})).status_code == 200
    await client.post(f"{P}/events/{eid}/submit", headers=owner)
    await client.post(f"{P}/events/{eid}/publish", headers=admin)
    assert (await client.post(f"{P}/events/{eid}/registrations", headers=user)).status_code == 422
    await client.patch(f"{P}/me", headers=user, json={"grade": 8})
    assert (await client.post(f"{P}/events/{eid}/registrations", headers=user)).status_code == 422
    await client.patch(f"{P}/me", headers=user, json={"grade": 10})
    assert (await client.post(f"{P}/events/{eid}/registrations", headers=user)).status_code == 201
    await client.delete(f"{P}/events/{eid}/registrations/me", headers=user)
    deadline = datetime.fromisoformat(body["starts_at"]) - timedelta(days=20)
    await client.patch(f"{P}/events/{eid}", headers=owner, json={"registration_deadline": deadline.isoformat()})
    await client.post(f"{P}/events/{eid}/publish", headers=admin)
    assert (await client.post(f"{P}/events/{eid}/registrations", headers=user)).status_code == 409
