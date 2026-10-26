from datetime import timedelta
from uuid import uuid4
from sqlalchemy import update
from core.time import utcnow
from db.models import Event, User
from .helpers import PREFIX as P, account, event_setup


async def test_private_dialog_and_read_receipts(api):
    c=api[0]
    admin,owner,eid,_=await event_setup(api)
    student,profile,_=await account(api)
    stranger,_,_=await account(api,'stranger')
    start=await c.post(f'{P}/events/{eid}/conversation',headers=student)
    assert start.status_code==200,start.text
    cid=start.json()['id']
    assert (await c.post(f'{P}/events/{eid}/conversation',headers=student)).json()['id']==cid
    assert (await c.post(f'{P}/events/{eid}/conversation',headers=owner)).status_code==409
    for headers in (stranger,admin):
        assert (await c.get(f'{P}/conversations/{cid}/messages',headers=headers)).status_code==404
        assert (await c.post(f'{P}/conversations/{cid}/messages',headers=headers,json={'body':'Чужое','client_id':str(uuid4())})).status_code==404
    payload={'body':'Можно прийти с другом?','client_id':str(uuid4())}
    sent=await c.post(f'{P}/conversations/{cid}/messages',headers=student,json=payload)
    assert sent.status_code==200,sent.text
    mid=sent.json()['id']
    assert (await c.post(f'{P}/conversations/{cid}/messages',headers=student,json=payload)).json()['id']==mid
    assert (await c.post(f'{P}/conversations/{cid}/messages',headers=student,json={**payload,'body':'Другой текст'})).status_code==409
    assert (await c.get(P+'/me/communications/summary',headers=owner)).json()['messages']==1
    listed=(await c.get(P+'/me/conversations',headers=owner)).json()['items'][0]
    assert listed['partner_name']==profile['name'] and listed['unread']==1
    assert (await c.post(f'{P}/conversations/{cid}/read',headers=owner,json={'message_id':mid})).status_code==204
    assert (await c.get(P+'/me/communications/summary',headers=owner)).json()['messages']==0
    reply=await c.post(f'{P}/conversations/{cid}/messages',headers=owner,json={'body':'Да!','client_id':str(uuid4())})
    assert reply.status_code==200
    assert (await c.get(P+'/me/communications/summary',headers=student)).json()['messages']==1
    assert (await c.get(f'{P}/conversations/{cid}/messages',headers=student,params={'after_id':mid})).json()['items'][0]['body']=='Да!'
    assert (await c.delete(f'{P}/events/{eid}',headers=admin)).status_code==204
    history=await c.get(f'{P}/conversations/{cid}/messages',headers=student)
    assert len(history.json()['items'])==2
    assert (await c.get(P+'/me/conversations',headers=student)).json()['items'][0]['event_id'] is None


async def test_message_validation_pagination_and_disabled_partner(api):
    c,factory,_=api
    _,owner,eid,_=await event_setup(api)
    user,profile,_=await account(api)
    cid=(await c.post(f'{P}/events/{eid}/conversation',headers=user)).json()['id']
    for text in ('   ','x'*4001):
        assert (await c.post(f'{P}/conversations/{cid}/messages',headers=user,json={'body':text,'client_id':str(uuid4())})).status_code==422
    ids=[]
    for i in range(3):
        ids.append((await c.post(f'{P}/conversations/{cid}/messages',headers=user,json={'body':str(i),'client_id':str(uuid4())})).json()['id'])
    page=(await c.get(f'{P}/conversations/{cid}/messages',headers=owner,params={'limit':2})).json()
    assert page['has_more'] and [m['id'] for m in page['items']]==ids[1:]
    older=(await c.get(f'{P}/conversations/{cid}/messages',headers=owner,params={'before_id':ids[1]})).json()
    assert [m['id'] for m in older['items']]==ids[:1]
    assert (await c.post(f'{P}/conversations/{cid}/read',headers=owner,json={'message_id':999999})).status_code==404
    async with factory.begin() as db:
        await db.execute(update(User).where(User.id==profile['id']).values(is_active=False))
    assert (await c.post(f'{P}/conversations/{cid}/messages',headers=owner,json={'body':'test','client_id':str(uuid4())})).status_code==409


async def test_reminder_due_read_reschedule_cancel_and_remove(api):
    c,factory,_=api
    _,owner,eid,_=await event_setup(api)
    user,_,_=await account(api)
    other,_,_=await account(api,'other')
    await c.put(f'{P}/me/plans/{eid}',headers=user,json={'reminder_minutes_before':60})
    assert (await c.get(P+'/me/reminders',headers=user)).json()['total']==0
    now=utcnow()
    async with factory.begin() as db:
        await db.execute(update(Event).where(Event.id==eid).values(starts_at=now+timedelta(minutes=30),ends_at=now+timedelta(hours=2)))
    reminder=(await c.get(P+'/me/reminders',headers=user)).json()['items'][0]
    assert reminder['unread'] and reminder['minutes_before']==60
    assert (await c.get(P+'/me/reminders',headers=other)).json()['total']==0
    assert (await c.post(f'{P}/me/reminders/{eid}/read',headers=other,json={'due_at':reminder['due_at']})).status_code==404
    assert (await c.post(f'{P}/me/reminders/{eid}/read',headers=user,json={'due_at':reminder['due_at']})).status_code==204
    assert (await c.get(P+'/me/communications/summary',headers=user)).json()['reminders']==0
    async with factory.begin() as db:
        await db.execute(update(Event).where(Event.id==eid).values(starts_at=now+timedelta(minutes=20)))
    assert (await c.get(P+'/me/communications/summary',headers=user)).json()['reminders']==1
    assert (await c.post(f'{P}/me/reminders/{eid}/read',headers=user,json={'due_at':reminder['due_at']})).status_code==409
    await c.put(f'{P}/me/plans/{eid}',headers=user,json={'reminder_minutes_before':None})
    assert (await c.get(P+'/me/reminders',headers=user)).json()['total']==0
    await c.put(f'{P}/me/plans/{eid}',headers=user,json={'reminder_minutes_before':60})
    await c.post(f'{P}/events/{eid}/cancel',headers=owner)
    assert (await c.get(P+'/me/reminders',headers=user)).json()['total']==0
    await c.delete(f'{P}/me/plans/{eid}',headers=user)
    assert (await c.get(P+'/me/reminders',headers=user)).json()['total']==0


async def test_communications_require_login(api):
    for route in ('/me/communications/summary','/me/conversations','/me/reminders','/conversations/1/messages'):
        assert (await api[0].get(P+route)).status_code==401
