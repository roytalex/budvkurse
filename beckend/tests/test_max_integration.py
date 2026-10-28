from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit
import jwt
from core.config import get_settings
from core.errors import AppError
from services import max_bot
from .helpers import PREFIX as P, account, event_setup
from .test_achievements import finish


async def test_certificate_link_requires_owner_attendance_and_expires(api):
    client=api[0]
    _, owner, eid, _=await event_setup(api, capacity=3)
    student,user,_=await account(api,'certificate-owner')
    other,_,_=await account(api,'certificate-other')
    path=f'{P}/events/{eid}/certificate-link'
    assert (await client.post(path)).status_code==401
    assert (await client.post(path,headers=student)).status_code==409
    await client.post(f'{P}/events/{eid}/registrations',headers=student)
    await finish(api,eid)
    await client.put(f'{P}/events/{eid}/attendance/{user["id"]}',headers=owner,json={'attended':True})
    assert (await client.post(path,headers=other)).status_code==409
    issued=await client.post(path,headers=student)
    assert issued.status_code==200 and issued.headers['cache-control']=='no-store'
    link=issued.json()['path']
    result=await client.get(link)
    assert result.status_code==200 and user['name'] in result.text
    assert result.headers['cache-control']=='no-store' and result.headers['referrer-policy']=='no-referrer'
    token=parse_qs(urlsplit(link).query)['token'][0]
    assert (await client.get(P+'/me',headers={'Authorization':'Bearer '+token})).status_code==401
    claims=jwt.decode(token,get_settings().jwt_secret,algorithms=['HS256'])
    claims['exp']=datetime.now(timezone.utc)-timedelta(seconds=1)
    expired=jwt.encode(claims,get_settings().jwt_secret,algorithm='HS256')
    assert (await client.get(P+'/exports/certificate',params={'token':expired})).status_code==401
    assert (await client.get(P+'/exports/certificate',params={'token':token+'x'})).status_code==401
    await client.put(f'{P}/events/{eid}/attendance/{user["id"]}',headers=owner,json={'attended':False})
    assert (await client.get(link)).status_code==409


async def test_webhook_secret_commands_and_retries(api,monkeypatch):
    client=api[0];settings=get_settings()
    url=P+'/integrations/max/webhook'
    assert (await client.post(url,json={})).status_code==503
    monkeypatch.setattr(settings,'max_bot_token','test-bot-token')
    monkeypatch.setattr(settings,'max_bot_username','test_school_bot')
    monkeypatch.setattr(settings,'max_webhook_secret','test-webhook-secret-with-at-least-32-characters')
    headers={'X-Max-Bot-Api-Secret':settings.max_webhook_secret}
    max_bot.completed.clear();max_bot.pending.clear();calls=[]
    def send(path,body,query):
        calls.append((path,body,query))
        return {'message':{'body':{'mid':'test'}}}
    monkeypatch.setattr(max_bot,'api_call',send)
    update={'update_type':'bot_started','timestamp':1,'user':{'user_id':123,'is_bot':False}}
    assert (await client.post(url,json=update)).status_code==403
    for _ in range(2):
        assert (await client.post(url,headers=headers,json=update)).status_code==200
    assert len(calls)==1 and calls[0][2]['user_id']==123
    button=calls[0][1]['attachments'][0]['payload']['buttons'][0][0]
    assert button=={'type':'open_app','text':'Открыть приложение','web_app':'test_school_bot','payload':'feed'}
    message={'update_type':'message_created','message':{'sender':{'user_id':321,'is_bot':False},'recipient':{'chat_type':'chat'},'body':{'text':'/start','mid':'m1'}}}
    assert (await client.post(url,headers=headers,json=message)).status_code==200
    assert len(calls)==1
    message['message']['recipient']['chat_type']='dialog'
    assert (await client.post(url,headers=headers,json=message)).status_code==200
    assert len(calls)==2
    message['message']['body']['text']='произвольный текст'
    assert (await client.post(url,headers=headers,json=message)).status_code==200
    assert len(calls)==2
    assert (await client.post(url,headers=headers,json={'message':{'body':[]}})).status_code==422
    assert (await client.post(url,headers=headers,content=b'x'*65537)).status_code==413
    def fail(*args):raise AppError(502,'Test failure')
    monkeypatch.setattr(max_bot,'api_call',fail)
    update['timestamp']=2
    assert (await client.post(url,headers=headers,json=update)).status_code==502
    assert not max_bot.pending
    monkeypatch.setattr(max_bot,'api_call',send)
    assert (await client.post(url,headers=headers,json=update)).status_code==200
    assert len(calls)==3
