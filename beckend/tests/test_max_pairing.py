import asyncio
import hashlib
from datetime import timedelta
from urllib.error import HTTPError
from unittest.mock import AsyncMock
import pytest
from sqlalchemy import select
from core.config import get_settings
from core.errors import AppError
from core.time import utcnow
from db.models import MaxLink, MaxConnection, Plan
from services import max_bot, max_pairing, max_notifications
from .helpers import PREFIX as P, account
from .test_max_notifications import configure, due_setup


def bot_config(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(get_settings(), 'max_webhook_secret', 'test-webhook-secret-at-least-thirty-two-chars')
    monkeypatch.setattr(max_bot, 'SEND_INTERVAL', 0)
    max_bot.completed.clear()
    return {'X-Max-Bot-Api-Secret': get_settings().max_webhook_secret}


def callback(code, mid='cb1', max_id=12345):
    return {'update_type':'message_callback', 'callback':{'callback_id':mid,'payload':'connect_'+code,'user':{'user_id':max_id}}, 'message':{'recipient':{'chat_type':'dialog'}}}


async def test_browser_pairing_requires_login_and_confirmation_and_survives_redelivery(api, monkeypatch):
    headers = bot_config(monkeypatch)
    client = api[0]
    user_headers, user, _ = await account(api)
    path = P+'/integrations/max/connection'
    assert (await client.post(path+'/link')).status_code == 401
    issued = await client.post(path+'/link', headers=user_headers)
    assert issued.status_code == 200 and issued.headers['cache-control'] == 'no-store'
    code = issued.json()['command'].split()[1]
    assert issued.json()['url'].endswith('?start=connect_'+code)
    async with api[1]() as db:
        link = await db.get(MaxLink, user['id'])
        assert link.token_hash == hashlib.sha256(code.encode()).hexdigest()
        assert link.token_hash != code and link.used_by is None
    calls=[]
    def send(path, body, query):
        calls.append((path,body,query))
        return {'success':True} if path=='/answers' else {'message':{'body':{'mid':'ok'}}}
    monkeypatch.setattr(max_bot, 'api_call', send)
    started={'update_type':'bot_started','user':{'user_id':12345},'payload':'connect_'+code}
    assert (await client.post(P+'/integrations/max/webhook',json=started,headers=headers)).status_code==200
    assert 'Подключить напоминания' in str(calls[-1][1])
    assert not (await client.get(path, headers=user_headers)).json()['connected']
    assert (await client.post(P+'/integrations/max/webhook',json=callback(code),headers=headers)).status_code==200
    assert (await client.get(path,headers=user_headers)).json()['enabled']
    max_bot.completed.clear()
    assert (await client.post(P+'/integrations/max/webhook',json=callback(code),headers=headers)).status_code==200
    assert 'Готово!' in calls[-1][1]['message']['text']
    await max_notifications.stop_for_max(12345)
    assert (await client.post(P+'/integrations/max/webhook',json=callback(code,'cb2'),headers=headers)).status_code==200
    assert not (await client.get(path,headers=user_headers)).json()['enabled']
    assert 'уже использована' in calls[-1][1]['message']['text']


async def test_pairing_expiry_rotation_revocation_and_account_conflicts(api, monkeypatch):
    bot_config(monkeypatch)
    client=api[0]
    first,user,_=await account(api)
    second,other,_=await account(api,'other')
    path=P+'/integrations/max/connection'
    async def issue(headers):
        return (await client.post(path+'/link',headers=headers)).json()['command'].split()[1]
    old=await issue(first);code=await issue(first)
    with pytest.raises(AppError):await max_pairing.confirm(old,12345)
    with pytest.raises(AppError):await max_pairing.confirm('wrong',12345)
    async with api[1].begin() as db:
        link=await db.get(MaxLink,user['id']);link.expires_at=utcnow()-timedelta(seconds=1)
    with pytest.raises(AppError):await max_pairing.confirm(code,12345)
    code=await issue(first);await max_pairing.confirm(code,12345)
    with pytest.raises(AppError):await max_pairing.confirm(code,999)
    other_code=await issue(second)
    with pytest.raises(AppError) as error:await max_pairing.confirm(other_code,12345)
    assert error.value.status==409
    fresh=await issue(first)
    assert (await client.delete(path,headers=first)).status_code==204
    with pytest.raises(AppError):await max_pairing.confirm(fresh,12345)
    await max_pairing.confirm(other_code,12345)
    assert (await client.get(path,headers=second)).json()['enabled']
    cancelled=await issue(first)
    assert (await client.delete(path+'/link',headers=first)).status_code==204
    with pytest.raises(AppError):await max_pairing.confirm(cancelled,999)


async def test_stop_events_are_silent_and_start_does_not_reenable(api, monkeypatch):
    headers=bot_config(monkeypatch)
    student,_,_,_=await due_setup(api,monkeypatch)
    calls=[]
    monkeypatch.setattr(max_bot,'api_call',lambda *args:calls.append(args) or {'message':{'body':{'mid':'ok'}}})
    for kind in ('bot_stopped','dialog_removed'):
        event={'update_type':kind,'user':{'user_id':12345}}
        assert (await api[0].post(P+'/integrations/max/webhook',json=event,headers=headers)).status_code==200
    assert calls==[]
    assert not (await api[0].get(P+'/integrations/max/connection',headers=student)).json()['enabled']
    await max_bot.process({'update_type':'bot_started','user':{'user_id':12345}})
    assert 'приостановлены' in await max_notifications.bot_summary(12345)


async def test_delivery_respects_retry_after_and_disables_forbidden_recipient(api, monkeypatch):
    bot_config(monkeypatch)
    _,_,_,pid=await due_setup(api,monkeypatch)
    def limited(*args):raise max_bot.MaxAPIError('limited',429,900)
    monkeypatch.setattr(max_bot,'api_call',limited)
    assert await max_notifications.deliver_one(api[1],pid)
    async with api[1].begin() as db:
        plan=await db.get(Plan,pid)
        assert (max_notifications.aware(plan.max_retry_at)-utcnow()).total_seconds()>890
        assert plan.max_sent_at is None
        plan.max_retry_at=utcnow()-timedelta(seconds=1)
    def blocked(*args):raise max_bot.MaxAPIError('blocked',403)
    monkeypatch.setattr(max_bot,'api_call',blocked)
    assert await max_notifications.deliver_one(api[1],pid)
    assert not await max_notifications.deliver_one(api[1],pid)
    async with api[1]() as db:
        assert not (await db.scalar(select(MaxConnection))).enabled


async def test_invalid_callbacks_rejected_and_group_cannot_pair(api, monkeypatch):
    headers=bot_config(monkeypatch)
    client=api[0]
    path=P+'/integrations/max/webhook'
    for body in ({'callback':[]},{'callback':{'user':[],'callback_id':'id','payload':'a'}},{'payload':{}},{'callback':{'user':{},'callback_id':'','payload':'a'}}):
        assert (await client.post(path,json=body,headers=headers)).status_code==422
    forbidden=AsyncMock(side_effect=AssertionError('Must not connect'))
    monkeypatch.setattr(max_pairing,'confirm',forbidden)
    body=callback('a'*32);body['message']['recipient']['chat_type']='chat'
    assert (await client.post(path,json=body,headers=headers)).status_code==200
    forbidden.assert_not_called()


async def test_sender_requires_confirmation_and_deduplicates_message_id(monkeypatch):
    bot_config(monkeypatch)
    message={'update_type':'message_created','message':{'sender':{'user_id':20},'recipient':{'chat_type':'dialog'},'body':{'mid':'unique','text':'/start'}}}
    monkeypatch.setattr(max_bot,'api_call',lambda *args:{})
    with pytest.raises(AppError):await max_bot.process(message)
    calls=[]
    monkeypatch.setattr(max_bot,'api_call',lambda *args:calls.append(args) or {'message':{}})
    await max_bot.process(message)
    message['timestamp']=123
    await max_bot.process(message)
    assert len(calls)==1


async def test_same_recipient_sends_are_serialized(monkeypatch):
    monkeypatch.setattr(max_bot,'SEND_INTERVAL',0.04)
    max_bot.last_sent.clear()
    moments=[]
    def send(*args):
        moments.append(max_bot.time.monotonic())
        return {'message':{}}
    monkeypatch.setattr(max_bot,'api_call',send)
    await asyncio.gather(*(max_bot.send_message(42,{'text':'test'}) for _ in range(3)))
    assert len(moments)==3 and all(b-a>=0.03 for a,b in zip(moments,moments[1:]))


async def test_two_max_users_cannot_consume_the_same_link(api, monkeypatch):
    bot_config(monkeypatch)
    headers,user,_=await account(api)
    response=await api[0].post(P+'/integrations/max/connection/link',headers=headers)
    code=response.json()['command'].split()[1]
    results=await asyncio.gather(max_pairing.confirm(code,12345),max_pairing.confirm(code,999),return_exceptions=True)
    assert sum(result is None for result in results)==1
    assert sum(isinstance(result,AppError) for result in results)==1
    async with api[1]() as db:
        connection=await db.get(MaxConnection,user['id'])
        link=await db.get(MaxLink,user['id'])
        assert link.used_by==connection.max_user_id


def test_http_rate_limit_is_safe_and_retains_retry_after(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(get_settings(),'max_ca_bundle',None)
    def fail(*args,**kwargs):
        raise HTTPError('https://platform-api2.max.ru/messages',429,'private upstream body',{'Retry-After':'120'},None)
    monkeypatch.setattr(max_bot,'urlopen',fail)
    with pytest.raises(max_bot.MaxAPIError) as error:max_bot.api_call('/messages',{'text':'test'})
    assert error.value.upstream_status==429 and error.value.retry_after==120
    assert 'private' not in error.value.detail
