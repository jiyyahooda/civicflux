"""Independent civilian sessions, SMS challenges and owner-only profile storage."""
import hashlib,hmac,json,os,re,secrets,time
from uuid import uuid4
import httpx
from fastapi import APIRouter,Depends,HTTPException,Request,Response
from pydantic import BaseModel,Field,ConfigDict,field_validator
from email_validator import validate_email,EmailNotValidError
from backend.auth import same_origin
from backend.db.connection import connection
router=APIRouter(prefix='/api/civilian',tags=['Civilian portal'])
COOKIE='civicflux_civilian'; CHALLENGE='civicflux_otp_browser'
class PaymentRequired(HTTPException):
 """Provider explicitly rejected delivery before dispatch."""
 def __init__(self):super().__init__(503,'Fast2SMS requires a first wallet transaction of at least INR 100 before API sending is enabled. No OTP was sent. The account owner must complete activation, then request a new code.')

def initialize():
 with connection() as db:db.executescript('''
 CREATE TABLE IF NOT EXISTS civilian_users(id TEXT PRIMARY KEY,phone TEXT NOT NULL UNIQUE,name TEXT NOT NULL,email TEXT NOT NULL DEFAULT '',address TEXT NOT NULL DEFAULT '',created REAL NOT NULL);
 CREATE TABLE IF NOT EXISTS civilian_sessions(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES civilian_users(id),expires REAL NOT NULL,last_seen REAL NOT NULL);
 CREATE TABLE IF NOT EXISTS civilian_otp(id TEXT PRIMARY KEY,phone TEXT NOT NULL,name TEXT NOT NULL,browser_hash TEXT NOT NULL,code_hash TEXT NOT NULL,created REAL NOT NULL,expires REAL NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,state TEXT NOT NULL,ip_hash TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS civilian_saved(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES civilian_users(id),kind TEXT NOT NULL,body TEXT NOT NULL,created REAL NOT NULL);
 CREATE INDEX IF NOT EXISTS civilian_otp_phone ON civilian_otp(phone,created);
 CREATE INDEX IF NOT EXISTS civilian_saved_owner ON civilian_saved(user_id,kind);
 ''')

def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def code_digest(id,code):return hmac.new(os.environ['FAST2SMS_API_KEY'].encode(),(id+':'+code).encode(),hashlib.sha256).hexdigest()
def sms_mode():return os.getenv('FAST2SMS_MODE','smart').strip().lower()
def configured():return bool(os.getenv('FAST2SMS_API_KEY') and (sms_mode()=='quick' or sms_mode()=='smart' and os.getenv('FAST2SMS_OTP_TEMPLATE_ID')))
def profile(row):return {k:row[k] for k in ('id','phone','name','email','address')}
def identity(request:Request):
 token=request.cookies.get(COOKIE,'')
 if not token:raise HTTPException(401,'Login first using your phone number and SMS OTP.')
 clock=time.time()
 with connection() as db:
  row=db.execute('SELECT u.*,s.expires,s.last_seen FROM civilian_sessions s JOIN civilian_users u ON u.id=s.user_id WHERE token_hash=?',(digest(token),)).fetchone()
  if not row or row['expires']<clock or clock-row['last_seen']>86400:raise HTTPException(401,'Your civilian session expired. Login again.')
  db.execute('UPDATE civilian_sessions SET last_seen=? WHERE token_hash=?',(clock,digest(token)))
 return profile(row)
def civilian(request:Request):same_origin(request);return identity(request)
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Send(Strict):
 name:str=Field(min_length=2,max_length=100)
 phone:str=Field(pattern=r'^[6-9][0-9]{9}$')
 @field_validator('name')
 @classmethod
 def valid_name(cls,v):
  v=v.strip()
  if len(v)<2:raise ValueError('Enter your name')
  return v
class Verify(Strict):
 challenge_id:str=Field(min_length=32,max_length=36)
 otp:str=Field(pattern=r'^[0-9]{6}$')
async def sms_send(phone,code):
 """Send one short OTP through the explicitly selected provider route; no fallback."""
 try:
  async with httpx.AsyncClient(timeout=15,follow_redirects=False) as client:
   if sms_mode()=='quick':
    r=await client.post('https://www.fast2sms.com/dev/bulkV2',headers={'Authorization':os.environ['FAST2SMS_API_KEY']},json={'route':'q','numbers':phone,'message':f'CivicFlux login code: {code}. Valid for 5 minutes. Do not share this code.','sms_details':'1'})
   else:
    r=await client.post('https://www.fast2sms.com/dev/otp/send',headers={'Authorization':os.environ['FAST2SMS_API_KEY']},json={'mobile':phone,'otp_id':os.environ['FAST2SMS_OTP_TEMPLATE_ID'],'otp':code,'otp_length':6,'otp_expiry':5})
   data=r.json()
 except Exception:raise HTTPException(503,'The SMS provider could not be reached or returned an invalid response. No automatic retry was made.') from None
 if not isinstance(data,dict):raise HTTPException(503,'The SMS provider returned an invalid response.')
 if r.status_code!=200 or data.get('return') is not True:
  if r.status_code==400 and str(data.get('status_code'))=='999':raise PaymentRequired()
  raise HTTPException(503,'SMS provider did not accept this request. Check account balance, selected SMS route permissions and provider configuration.')
@router.get('/session')
def session(request:Request,response:Response):
 try:user=identity(request)
 except HTTPException:
  user=None
  if request.cookies.get(COOKIE):response.delete_cookie(COOKIE)
 return {'user':user,'sms_configured':configured()}
@router.post('/otp/send')
async def send(body:Send,request:Request,response:Response):
 same_origin(request)
 if not configured():raise HTTPException(503,'SMS login is awaiting Fast2SMS setup. You can continue as guest.')
 clock=time.time();ip=digest(request.client.host if request.client else 'unknown');browser=secrets.token_urlsafe(32);id=uuid4().hex;code=f'{secrets.randbelow(1000000):06d}'
 with connection() as db:
  db.execute('BEGIN IMMEDIATE')
  if sms_mode()=='quick':
   try:limit=int(os.getenv('FAST2SMS_QUICK_LIMIT','1'));activated=float(os.getenv('FAST2SMS_QUICK_ACTIVATED_AT','0'))
   except ValueError:raise HTTPException(503,'Invalid SMS budget configuration.')
   used=db.execute("SELECT count(*) FROM civilian_otp WHERE created>=? AND state!='payment_required'",(activated,)).fetchone()[0]
   if limit<1 or used>=limit:raise HTTPException(429,'The approved Quick SMS message budget has been used. Further sends need owner approval.')
  recent=db.execute('SELECT created FROM civilian_otp WHERE phone=? ORDER BY created DESC LIMIT 1',(body.phone,)).fetchone()
  phone_count=db.execute('SELECT count(*) FROM civilian_otp WHERE created>? AND phone=?',(clock-3600,body.phone)).fetchone()[0]
  ip_count=db.execute('SELECT count(*) FROM civilian_otp WHERE created>? AND ip_hash=?',(clock-3600,ip)).fetchone()[0]
  if (recent and clock-recent['created']<60) or phone_count>=5 or ip_count>=20:raise HTTPException(429,'Please wait before requesting another OTP. Maximum five requests per hour.')
  db.execute("UPDATE civilian_otp SET state='superseded' WHERE phone=? AND state IN ('pending','sent')",(body.phone,))
  db.execute('INSERT INTO civilian_otp VALUES (?,?,?,?,?,?,?,?,?,?)',(id,body.phone,body.name,digest(browser),code_digest(id,code),clock,clock+300,0,'pending',ip))
  # Retain attempt history so expiry cannot reset the approved SMS spend cap.
 try:await sms_send(body.phone,code)
 except HTTPException as error:
  # Only a confirmed activation rejection releases the paid-send allowance.
  # Ambiguous failures (including network timeouts) still consume it.
  state='payment_required' if isinstance(error,PaymentRequired) else 'failed'
  with connection() as db:db.execute('UPDATE civilian_otp SET state=? WHERE id=?',(state,id))
  raise
 with connection() as db:db.execute("UPDATE civilian_otp SET state='sent' WHERE id=? AND state='pending'",(id,))
 response.set_cookie(CHALLENGE,browser,httponly=True,secure=request.url.scheme=='https',samesite='strict',max_age=300,path='/api/civilian')
 response.headers['Cache-Control']='no-store'
 return {'challenge_id':id,'expires_in':300,'retry_after':60,'status':'provider_accepted','message':'Fast2SMS accepted the SMS request. Enter the code when it arrives.'}
@router.post('/otp/verify')
def verify(body:Verify,request:Request,response:Response):
 same_origin(request);clock=time.time();user=None
 with connection() as db:
  db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM civilian_otp WHERE id=?',(body.challenge_id,)).fetchone()
  if not row or not hmac.compare_digest(row['browser_hash'],digest(request.cookies.get(CHALLENGE,''))):raise HTTPException(400,'Invalid or expired OTP request. Request a new code.')
  if row['state']!='sent' or row['expires']<clock or row['attempts']>=5:raise HTTPException(400,'OTP expired or unavailable. Request a new code.')
  db.execute('UPDATE civilian_otp SET attempts=attempts+1 WHERE id=?',(row['id'],))
  match=configured() and hmac.compare_digest(row['code_hash'],code_digest(row['id'],body.otp))
  if match:
   db.execute("UPDATE civilian_otp SET state='used' WHERE id=?",(row['id'],))
   db.execute('INSERT OR IGNORE INTO civilian_users(id,phone,name,created) VALUES (?,?,?,?)',(uuid4().hex,row['phone'],row['name'],clock))
   user=profile(db.execute('SELECT * FROM civilian_users WHERE phone=?',(row['phone'],)).fetchone())
   token=secrets.token_urlsafe(32)
   db.execute('DELETE FROM civilian_sessions WHERE expires<?',(clock,))
   db.execute('INSERT INTO civilian_sessions VALUES (?,?,?,?)',(digest(token),user['id'],clock+604800,clock))
 if user is None:raise HTTPException(400,'Incorrect OTP. Check the SMS and try again.')
 response.set_cookie(COOKIE,token,httponly=True,secure=request.url.scheme=='https',samesite='strict',max_age=604800)
 response.delete_cookie(CHALLENGE,path='/api/civilian');response.headers['Cache-Control']='no-store'
 return {'user':user}
@router.post('/logout')
def logout(request:Request,response:Response):
 same_origin(request)
 with connection() as db:db.execute('DELETE FROM civilian_sessions WHERE token_hash=?',(digest(request.cookies.get(COOKIE,'')),))
 response.delete_cookie(COOKIE);return {'ok':True}
class Details(Strict):
 name:str=Field(min_length=2,max_length=100)
 email:str=Field(default='',max_length=254)
 address:str=Field(default='',max_length=400)
 @field_validator('name')
 @classmethod
 def name_trim(cls,v):
  if len(v.strip())<2:raise ValueError('Enter your name')
  return v.strip()
 @field_validator('email')
 @classmethod
 def email_check(cls,v):
  if not v.strip():return ''
  try:return validate_email(v,check_deliverability=False).normalized
  except EmailNotValidError:raise ValueError('Enter a valid email')
@router.post('/profile')
def update(body:Details,user=Depends(civilian)):
 with connection() as db:db.execute('UPDATE civilian_users SET name=?,email=?,address=? WHERE id=?',(body.name,body.email,body.address.strip(),user['id']))
 return {**user,**body.model_dump()}
@router.get('/reports')
def reports(user=Depends(civilian)):
 from backend.api.civic import public_report
 with connection() as db:rows=db.execute("SELECT body FROM records WHERE kind='complaint' AND json_extract(body,'$.civilian_id')=? ORDER BY created DESC",(user['id'],)).fetchall()
 return [public_report(json.loads(r['body'])) for r in rows]
class Point(Strict):
 latitude:float=Field(ge=-90,le=90)
 longitude:float=Field(ge=-180,le=180)
 label:str=Field(min_length=1,max_length=200)
 place_id:str|None=Field(default=None,max_length=200)
class Saved(Strict):
 kind:str=Field(pattern=r'^(place|route)$')
 label:str=Field(min_length=1,max_length=80)
 points:list[Point]=Field(min_length=1,max_length=7)
 @field_validator('label')
 @classmethod
 def label_trim(cls,v):
  if not v.strip():raise ValueError('Enter a label')
  return v.strip()
@router.get('/saved')
def saved(user=Depends(civilian)):
 with connection() as db:rows=db.execute('SELECT id,kind,body FROM civilian_saved WHERE user_id=? ORDER BY created DESC',(user['id'],)).fetchall()
 return [{'id':r['id'],**json.loads(r['body'])} for r in rows]
@router.post('/saved',status_code=201)
def save(body:Saved,user=Depends(civilian)):
 if (body.kind=='place' and len(body.points)!=1) or (body.kind=='route' and len(body.points)<2):raise HTTPException(422,'Choose one place or at least two route points.')
 id=uuid4().hex
 with connection() as db:
  if db.execute('SELECT count(*) FROM civilian_saved WHERE user_id=?',(user['id'],)).fetchone()[0]>=50:raise HTTPException(409,'You can keep up to 50 saved places and routes.')
  db.execute('INSERT INTO civilian_saved VALUES (?,?,?,?,?)',(id,user['id'],body.kind,json.dumps(body.model_dump(),allow_nan=False),time.time()))
 return {'id':id,**body.model_dump()}
@router.delete('/saved/{id}')
def remove(id:str,user=Depends(civilian)):
 with connection() as db:
  if not db.execute('DELETE FROM civilian_saved WHERE id=? AND user_id=?',(id,user['id'])).rowcount:raise HTTPException(404,'Saved item not found')
 return {'ok':True}
