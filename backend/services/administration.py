"""Database-backed identities and deny-by-default municipal jurisdiction checks."""
import hashlib
import hmac
import secrets
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import HTTPException
from backend.db.connection import connection
from backend import config


def hash_password(password):
    if not 3 <= len(password) <= 1024:raise ValueError('Password must contain 3–1024 characters')
    salt=secrets.token_bytes(16)
    digest=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1,dklen=32)
    return 'scrypt$16384$8$1$'+salt.hex()+'$'+digest.hex()


def verify_password(password,encoded):
    try:
        algorithm,n,r,p,salt,digest=encoded.split('$')
        if algorithm!='scrypt' or (int(n),int(r),int(p))!=(16384,8,1) or len(password)>1024:return False
        return hmac.compare_digest(hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=int(n),r=int(r),p=int(p),dklen=32).hex(),digest)
    except (ValueError,TypeError):return False


def bootstrap():
    if not config.ADMIN_PASSWORD:return
    with connection() as db:
        if db.execute('SELECT 1 FROM admin_users WHERE username=?',(config.ADMIN_ID,)).fetchone():return
        identifier=str(uuid4());stamp=datetime.now(timezone.utc).isoformat()
        db.execute('INSERT INTO admin_users(id,username,password_hash,display_name,role,created_at) VALUES (?,?,?,?,?,?)',
          (identifier,config.ADMIN_ID,hash_password(config.ADMIN_PASSWORD),'Local supervisor','system_supervisor',stamp))
        for c in db.execute('SELECT id FROM cities').fetchall():db.execute('INSERT INTO admin_city_assignments VALUES (?,?)',(identifier,c['id']))


def area_identity(actor):
    if not actor.startswith('area:'):return None
    with connection() as db:row=db.execute('SELECT * FROM admins WHERE id=? AND is_active=1',(actor[5:],)).fetchone()
    if not row:raise HTTPException(401,'Administrator account is inactive')
    u=dict(row)
    return {**u,'display_name':u['area_name'],'role':'area_admin','cities':[u['city_id']],
      'assignments':[{'pincode':u['pincode'],'city_id':u['city_id'],'locality_name':u['area_name']}]}

def identity(actor):
    scoped=area_identity(actor)
    if scoped:return scoped
    with connection() as db:
        row=db.execute('SELECT * FROM admin_users WHERE username=? AND is_active=1',(actor,)).fetchone()
        if not row:raise HTTPException(401,'Administrator account is inactive')
        user=dict(row)
        user['cities']=[r['city_id'] for r in db.execute('SELECT city_id FROM admin_city_assignments WHERE admin_id=?',(row['id'],))]
        user['assignments']=[dict(r) for r in db.execute('SELECT a.pincode,p.city_id,p.locality_name,a.assignment_role FROM admin_pincode_assignments a JOIN pincodes p ON p.pincode=a.pincode WHERE a.admin_id=? AND a.is_active=1 AND p.is_active=1',(row['id'],))]
        return user


def profile(actor):
    u=identity(actor)
    return {k:u[k] for k in ('id','username','display_name','role','cities','assignments','pincode','area_name','city_id','latitude','longitude','coordinate_source') if k in u}


def permitted(actor,city_id,pincode=None):
    u=identity(actor)
    if u['role']=='area_admin':return city_id==u['city_id'] and pincode in (None,u['pincode'])
    if u['role']=='system_supervisor':return True
    if u['role']=='city_supervisor' and city_id in u['cities']:return True
    return pincode is not None and any(a['city_id']==city_id and a['pincode']==pincode for a in u['assignments'])


def require_scope(actor,city_id,pincode=None):
    if not permitted(actor,city_id,pincode):raise HTTPException(403,'This city/PIN is outside your assigned jurisdiction')


def require_city(actor,city_id):
    u=identity(actor)
    if u['role']=='system_supervisor' or city_id in u['cities'] or any(a['city_id']==city_id for a in u['assignments']):return
    raise HTTPException(403,'This city is outside your assigned jurisdiction')


def record_pin(item):return item.get('pincode') or item.get('postal_code') or item.get('inputs',{}).get('pincode')
def visible(actor,item):
    u=identity(actor)
    if u['role']=='area_admin':return item.get('city_id')==u['city_id'] and record_pin(item)==u['pincode']
    return permitted(actor,item.get('city_id'),record_pin(item))
def require_record(actor,item):
    if not visible(actor,item):raise HTTPException(403,'Outside your assigned area')
def supervisor(actor):
    if identity(actor)['role']!='system_supervisor':raise HTTPException(403,'System supervisor permission required')


def provision(username,password,display_name,role='officer',pins=(),cities=(),performed_by='administrator_configuration'):
    if role not in {'officer','city_supervisor','system_supervisor'}:raise ValueError('Unsupported administrative role')
    if not username.strip() or len(username)>80:raise ValueError('Invalid username')
    if role=='officer' and not pins:raise ValueError('An officer requires at least one PIN assignment')
    if role=='city_supervisor' and not cities:raise ValueError('A city supervisor requires a city assignment')
    if len(password)<8:raise ValueError('New administrator passwords must contain at least eight characters')
    if password in pins:raise ValueError('A public PIN cannot be used as the password')
    encoded=hash_password(password);stamp=datetime.now(timezone.utc).isoformat()
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        if any(not db.execute('SELECT 1 FROM pincodes WHERE pincode=? AND is_active=1',(pin,)).fetchone() for pin in pins):raise ValueError('Unknown PIN assignment')
        if any(not db.execute('SELECT 1 FROM cities WHERE id=?',(cid,)).fetchone() for cid in cities):raise ValueError('Unknown city assignment')
        row=db.execute('SELECT id FROM admin_users WHERE username=?',(username,)).fetchone();identifier=row['id'] if row else str(uuid4())
        db.execute('INSERT INTO admin_users(id,username,password_hash,display_name,role,created_at) VALUES (?,?,?,?,?,?) ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash,display_name=excluded.display_name,role=excluded.role,is_active=1',
          (identifier,username,encoded,display_name,role,stamp))
        db.execute('DELETE FROM admin_pincode_assignments WHERE admin_id=?',(identifier,));db.execute('DELETE FROM admin_city_assignments WHERE admin_id=?',(identifier,))
        for pin in set(pins):db.execute('INSERT INTO admin_pincode_assignments VALUES (?,?,?,?,1)',(identifier,pin,'reviewer',stamp))
        for cid in set(cities):db.execute('INSERT INTO admin_city_assignments VALUES (?,?)',(identifier,cid))
        db.execute('DELETE FROM sessions WHERE actor=?',(username,))
        db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(stamp,performed_by,'admin_provisioned',identifier,'Role and geographic assignments configured; password not logged'))
    return profile(username)
