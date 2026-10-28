import hashlib, secrets, time
from urllib.parse import urlsplit
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from backend import config
from backend.db.connection import connection

router=APIRouter(prefix='/api/auth',tags=['authentication'])
class Login(BaseModel):
    username:str
    password:str

def same_origin(request:Request):
    # JSON mutations plus SameSite=Strict cookies prevent cross-site form requests.
    origin=request.headers.get('origin')
    parsed=urlsplit(origin or '')
    dev_proxy=(request.url.hostname in {'localhost','127.0.0.1'} and
               request.client is not None and request.client.host in {'127.0.0.1','::1','testclient'} and
               parsed.scheme=='http' and parsed.hostname==request.url.hostname and parsed.port in {5173,4173})
    if origin and origin.rstrip('/') != str(request.base_url).rstrip('/') and not dev_proxy:
        raise HTTPException(403,'Cross-origin admin request denied')

def admin(request:Request):
    same_origin(request)
    token=request.cookies.get('civicflux_session','')
    with connection() as db:
        row=db.execute('SELECT actor FROM sessions WHERE token_hash=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone()
    if not row: raise HTTPException(401,'Admin login required')
    from backend.services.administration import identity
    identity(row['actor'])
    return row['actor']

@router.post('/login')
def login(body:Login,response:Response,request:Request):
    same_origin(request)
    from backend.services.administration import verify_password,profile
    if len(body.password)>1024 or len(body.username)>80:raise HTTPException(401,'Invalid credentials')
    attempt_key=hashlib.sha256((body.username+'|'+str(request.client.host if request.client else '')).encode()).hexdigest()
    with connection() as db:
        attempt=db.execute('SELECT * FROM auth_attempts WHERE key=?',(attempt_key,)).fetchone()
        if attempt and attempt['failures']>=8 and time.time()-attempt['last_attempt']<300:raise HTTPException(429,'Too many login attempts. Try again in five minutes.')
        user=db.execute('SELECT * FROM admin_users WHERE username=? AND is_active=1',(body.username,)).fetchone()
    # Perform a password hash even for unknown names to reduce enumeration timing.
    encoded=user['password_hash'] if user else 'scrypt$16384$8$1$'+'00'*16+'$'+'00'*32
    valid=verify_password(body.password,encoded)
    if not user or not valid:
        with connection() as db:
            db.execute('INSERT INTO auth_attempts VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET failures=CASE WHEN excluded.last_attempt-auth_attempts.last_attempt>300 THEN 1 ELSE auth_attempts.failures+1 END,last_attempt=excluded.last_attempt',(attempt_key,time.time()))
        raise HTTPException(401,'Invalid credentials')
    with connection() as db:db.execute('DELETE FROM auth_attempts WHERE key=?',(attempt_key,))
    token=secrets.token_urlsafe(32)
    with connection() as db:
        db.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
        db.execute('INSERT INTO sessions VALUES (?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),body.username,time.time()+28800))
        from backend.db.repository import now
        db.execute('UPDATE admin_users SET last_login_at=? WHERE id=?',(now(),user['id']))
    response.set_cookie('civicflux_session',token,httponly=True,samesite='strict',secure=request.url.scheme=='https',max_age=28800)
    return {'role':'admin','actor':body.username,'profile':profile(body.username)}

@router.get('/me')
def me(actor:str=Depends(admin)):
    from backend.services.administration import profile
    return {'role':'admin','actor':actor,'profile':profile(actor)}

@router.post('/logout')
def logout(request:Request,response:Response):
    same_origin(request)
    with connection() as db: db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(request.cookies.get('civicflux_session','').encode()).hexdigest(),))
    response.delete_cookie('civicflux_session');return {'ok':True}
