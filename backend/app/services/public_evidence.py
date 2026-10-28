"""Small anonymous demonstration boundary: GET allowlist, global admission and safe buffered output."""
from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from threading import BoundedSemaphore, Lock
from time import monotonic

from starlette.responses import JSONResponse
from app.db.database import is_deployed_environment
from app.security.production_authorization import require_production_authorization

QUERY_DEADLINE = ContextVar('public_query_deadline', default=None)
REQUEST_SECONDS = 10
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
PUBLIC_PATH = re.compile(r'^/api/(?:drugs/search|drugs/[^/]+(?:/evidence|/safety/(?:labels|recalls|adverse_events))?|medications/overview|coverage(?:/inventory)?)$')


def safe_source_ids(value):
    if isinstance(value,list): return [safe_source_ids(item) for item in value]
    if isinstance(value,dict):
        return {key:('source:'+hashlib.sha256(item.encode()).hexdigest()
                     if key in {'source_id','source_record_id'} and isinstance(item,str)
                     and any(term in item for term in ('pharma_recovery','/Users/','/home/','data/'))
                     else safe_source_ids(item)) for key,item in value.items()}
    return value


class PublicEvidenceMiddleware:
    def __init__(self, app):
        self.app = app
        self.slots = BoundedSemaphore(2)
        self.overviews = BoundedSemaphore(1)
        self.lock = Lock()
        self.tokens, self.updated = 10.0, monotonic()

    def admit(self):
        with self.lock:
            now=monotonic()
            self.tokens=min(10.0,self.tokens+(now-self.updated))  # 60/minute, burst 10 globally.
            self.updated=now
            if self.tokens < 1: return False
            self.tokens-=1
            return True

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not is_deployed_environment():
            return await self.app(scope,receive,send)
        path, method = scope['path'], scope['method']
        async def error(status, detail):
            headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}
            if status==429: headers['Retry-After']='5'
            origin=dict(scope.get('headers',[])).get(b'origin',b'').decode('latin-1')
            allowed=[value.strip() for value in os.getenv('ALLOWED_ORIGINS','').split(',')]
            if origin and origin in allowed:
                headers.update({'Access-Control-Allow-Origin':origin,'Vary':'Origin'})
            await JSONResponse({'detail':detail},status_code=status,headers=headers)(scope,receive,send)
        # Liveness never opens data; readiness still requires a valid grant + artifact.
        if method=='GET' and path=='/':
            return await JSONResponse({'status':'ok','service':'Dav AI read-only evidence demonstration'})(scope,receive,send)
        if method=='GET' and path=='/health':
            return await self.app(scope,receive,send)
        try: grant=require_production_authorization()
        except Exception: return await error(503,'Public evidence service is unavailable')
        if not (path=='/ready' or PUBLIC_PATH.fullmatch(path)) or method not in {'GET','OPTIONS'}:
            return await error(403,'Operation is not available in the public demonstration')
        if len(scope.get('query_string',b'')) > 1024:
            return await error(400,'Query exceeds the public request limit')
        from urllib.parse import parse_qs
        params=parse_qs(scope.get('query_string',b'').decode('utf-8',errors='replace'),keep_blank_values=True)
        if any(len(values)!=1 for values in params.values()):
            return await error(400,'Repeated query fields are not supported')
        if path in {'/api/drugs/search','/api/medications/overview'}:
            if len(params.get('q',[''])[0].strip()) < 2:
                return await error(422,'Enter at least two characters')
            try:
                if not 1 <= int(params.get('limit',['20'])[0]) <= 20 or not 0 <= int(params.get('offset',['0'])[0]) <= 1000:
                    raise ValueError()
            except ValueError:
                return await error(422,'Public catalog pagination limit exceeded')
        if not self.admit(): return await error(429,'Evidence service is busy; retry shortly')
        if not self.slots.acquire(False): return await error(429,'Evidence service is busy; retry shortly')
        overview=path=='/api/medications/overview'
        if overview and not self.overviews.acquire(False):
            self.slots.release()
            return await error(429,'Evidence service is busy; retry shortly')
        remaining=(grant.expires_at-datetime.now(timezone.utc)).total_seconds()
        token=QUERY_DEADLINE.set(monotonic()+min(REQUEST_SECONDS,max(0,remaining)))
        messages=[]
        body=bytearray()
        async def buffer(message):
            if message['type']=='http.response.start': messages.append(message)
            elif message['type']=='http.response.body':
                chunk=message.get('body',b'')
                if len(body)+len(chunk)>MAX_RESPONSE_BYTES: raise ValueError('Bounded output exceeded')
                body.extend(chunk)
        try:
            await self.app(scope,receive,buffer)
            if monotonic()>=QUERY_DEADLINE.get(): raise TimeoutError()
            current=require_production_authorization()
            if current.payload_sha256!=grant.payload_sha256: raise ValueError('Grant changed')
            start=messages[0]
            if start['status']>=500: raise ValueError('Evidence read failed')
            headers=[(key,value) for key,value in start.get('headers',[]) if key.lower() not in {b'content-length',b'cache-control'}]
            if body and any(key.lower()==b'content-type' and b'application/json' in value for key,value in headers):
                body=bytearray(json.dumps(safe_source_ids(json.loads(body)),ensure_ascii=False,separators=(',',':')).encode())
            if len(body)>MAX_RESPONSE_BYTES: raise ValueError('Bounded output exceeded')
            headers.extend([(b'content-length',str(len(body)).encode()),(b'cache-control',b'no-store')])
            await send({**start,'headers':headers})
            await send({'type':'http.response.body','body':bytes(body)})
        except Exception:
            await error(503,'Public evidence service is unavailable')
        finally:
            QUERY_DEADLINE.reset(token)
            if overview: self.overviews.release()
            self.slots.release()
