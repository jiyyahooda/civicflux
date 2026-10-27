"""Small persistent cache for public provider responses; never stores API keys."""
import hashlib
import json
from datetime import datetime, timezone
import httpx
from backend.db.connection import connection


async def fetch_json(url, *, params=None, headers=None, ttl=300):
    public_params={k:v for k,v in (params or {}).items() if k.lower() not in {'api-key','apikey','api_key','key','token'}}
    key=hashlib.sha256(json.dumps([url,public_params],sort_keys=True).encode()).hexdigest()
    with connection() as db:
        db.execute('CREATE TABLE IF NOT EXISTS source_cache (key TEXT PRIMARY KEY, fetched_at TEXT NOT NULL, payload TEXT NOT NULL)')
        row=db.execute('SELECT fetched_at,payload FROM source_cache WHERE key=?',(key,)).fetchone()
    now=datetime.now(timezone.utc)
    if row and 0<=(now-datetime.fromisoformat(row['fetched_at'])).total_seconds()<ttl:
        return json.loads(row['payload']),row['fetched_at'],None
    error=None
    try:
        async with httpx.AsyncClient(timeout=18,follow_redirects=False) as client:
            response=await client.get(url,params=params,headers=headers)
        if response.status_code!=200:
            raise ValueError(f'Provider returned HTTP {response.status_code}; check provider access or try later')
        payload=response.json()
        stamp=datetime.now(timezone.utc).isoformat()
        with connection() as db:
            db.execute('INSERT OR REPLACE INTO source_cache VALUES (?,?,?)',(key,stamp,json.dumps(payload,allow_nan=False)))
        return payload,stamp,None
    except httpx.TimeoutException:
        error='Provider request timed out'
    except httpx.RequestError:
        error='Provider network request failed'
    except (ValueError,TypeError):
        error='Provider rejected the request or returned an invalid response'
    if row and (now-datetime.fromisoformat(row['fetched_at'])).total_seconds()<=86400:
        return json.loads(row['payload']),row['fetched_at'],error+'; showing last successful response'
    raise ValueError(error)
