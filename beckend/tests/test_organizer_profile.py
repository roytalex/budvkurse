import pytest
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from db.models import User
from .helpers import PREFIX as P, account, event_setup


async def test_organizer_has_no_student_fields_but_student_keeps_them(api):
    client = api[0]
    admin, owner, _, body = await event_setup(api)
    school = await client.post(P+'/schools', headers=admin, json={'city_id':body['city_id'], 'name':'Школа', 'address':'Учебная улица, 1'})
    assert school.status_code == 201, school.text
    sid = school.json()['id']
    for fields in ({'grade':8}, {'school_id':sid}, {'city_id':body['city_id'], 'grade':9, 'school_id':sid}):
        result = await client.patch(P+'/me', headers=owner, json=fields)
        assert result.status_code == 422, result.text
    result = await client.patch(P+'/me', headers=owner, json={'name':'Организатор', 'city_id':body['city_id'], 'max_contact_url':'@teacher'})
    assert result.status_code == 200, result.text
    assert result.json()['grade'] is None and result.json()['school_id'] is None
    assert result.json()['city_id'] == body['city_id']
    student, _, _ = await account(api)
    result = await client.patch(P+'/me', headers=student, json={'city_id':body['city_id'], 'school_id':sid, 'grade':8})
    assert result.status_code == 200, result.text
    assert result.json()['grade'] == 8 and result.json()['school_id'] == sid
    with pytest.raises(IntegrityError):
        async with api[1].begin() as db:
            await db.execute(update(User).where(User.role == 'organizer').values(grade=8))
