import hashlib,secrets,time
from urllib.parse import urlsplit
from fastapi import APIRouter,Depends,HTTPException,Request,Response
from pydantic import BaseModel,Field
from backend.db.connection import connection
from backend.db.repository import now
router=APIRouter(prefix='/api/auth',tags=['authentication'])
class Login(BaseModel):
 username:str=Field(max_length=80)
 password:str=Field(max_length=1024)
def same_origin(request):
 origin=request.headers.get('origin');parsed=urlsplit(origin or '')
 dev=request.url.hostname in {'localhost','127.0.0.1'} and request.client and request.client.host in {'127.0.0.1','::1','testclient'} and parsed.scheme=='http' and parsed.hostname==request.url.hostname and parsed.port in {5173,4173}
 if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/') and not dev:raise HTTPException(403,'Cross-origin admin request denied')
def resolve(request,touch=True):
 token=request.cookies.get('civicflux_session','')
 if not token:return None
 with connection() as db:
  row=db.execute('SELECT actor,expires,last_seen FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
  if not row or row['expires']<time.time() or time.time()-row['last_seen']>1800 or not row['actor'].startswith('area:'):return None
  from backend.services.administration import area_identity
  try:identity=area_identity(row['actor'])
  except HTTPException:return None
  if touch:db.execute('UPDATE sessions SET last_seen=? WHERE token_hash=?',(time.time(),hashlib.sha256(token.encode()).hexdigest()))
 return row['actor'],identity

def admin(request:Request):
 same_origin(request);session=resolve(request)
 if not session:raise HTTPException(401,'Admin login required')
 return session[0]
@router.post('/login')
def login(body:Login,response:Response,request:Request):
 same_origin(request);ip=request.client.host if request.client else 'unknown';clock=time.time()
 key=hashlib.sha256(('area-login:'+ip).encode()).hexdigest()
 with connection() as db:
  attempt=db.execute('SELECT * FROM auth_attempts WHERE key=?',(key,)).fetchone()
  if attempt and attempt['failures']>=5 and clock-attempt['last_attempt']<900:raise HTTPException(429,'Unable to sign in. Try again in fifteen minutes.')
  import re
  pin=body.password if re.fullmatch('[0-9]{6}',body.password) else None
  user=db.execute("SELECT * FROM admins WHERE username='admin' AND pincode=? AND is_active=1",(pin,)).fetchone() if body.username=='admin' else None
  db.execute('INSERT INTO area_login_audit(at,ip,pincode,success) VALUES (?,?,?,?)',(now(),ip,pin,int(user is not None)))
  if not user:
   db.execute('INSERT INTO auth_attempts VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET failures=CASE WHEN excluded.last_attempt-auth_attempts.last_attempt>=900 THEN 1 ELSE auth_attempts.failures+1 END,last_attempt=excluded.last_attempt',(key,clock))
  else:
   db.execute('DELETE FROM auth_attempts WHERE key=?',(key,));db.execute('UPDATE admins SET last_login_at=? WHERE id=?',(now(),user['id']))
 if not user:raise HTTPException(401,'Invalid credentials')
 token=secrets.token_urlsafe(32);actor='area:'+user['id']
 with connection() as db:
  db.execute('DELETE FROM sessions WHERE expires<?',(clock,))
  db.execute('INSERT INTO sessions(token_hash,actor,expires,last_seen) VALUES (?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),actor,clock+28800,clock))
 response.set_cookie('civicflux_session',token,httponly=True,samesite='strict',secure=request.url.scheme=='https',max_age=28800)
 from backend.services.administration import profile
 return {'role':'admin','actor':actor,'profile':profile(actor)}
@router.get('/me')
def me(actor:str=Depends(admin)):
 from backend.services.administration import profile
 return {'role':'admin','actor':actor,'profile':profile(actor)}
@router.post('/logout')
def logout(request:Request,response:Response):
 same_origin(request)
 with connection() as db:db.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(request.cookies.get('civicflux_session','').encode()).hexdigest(),))
 response.delete_cookie('civicflux_session');return {'ok':True}
