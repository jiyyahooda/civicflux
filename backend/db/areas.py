"""Area identities supersede legacy assignment accounts; retain historical rows."""
import json,re
from uuid import uuid4
from backend.db.connection import connection
from backend.db.repository import now
from project_paths import CONFIG

def migrate():
 with connection() as db:
  db.executescript("""CREATE TABLE IF NOT EXISTS admins(
  id TEXT PRIMARY KEY,username TEXT NOT NULL DEFAULT 'admin' CHECK(username='admin'),
  pincode TEXT NOT NULL UNIQUE CHECK(length(pincode)=6 AND pincode NOT GLOB '*[^0-9]*'),
  area_name TEXT NOT NULL,city_id TEXT NOT NULL REFERENCES cities(id),is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,last_login_at TEXT,latitude REAL,longitude REAL,coordinate_source TEXT);
  CREATE TABLE IF NOT EXISTS area_login_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT NOT NULL,ip TEXT NOT NULL,pincode TEXT,success INTEGER NOT NULL);
  CREATE INDEX IF NOT EXISTS area_login_ip ON area_login_audit(ip,at);
  CREATE TABLE IF NOT EXISTS area_assignment_migration(legacy_admin_id TEXT,pincode TEXT,area_admin_id TEXT,PRIMARY KEY(legacy_admin_id,pincode));""")
  jurisdiction_columns={row['name'] for row in db.execute('PRAGMA table_info(complaint_jurisdictions)')}
  if 'area_admin_id' not in jurisdiction_columns:db.execute('ALTER TABLE complaint_jurisdictions ADD COLUMN area_admin_id TEXT REFERENCES admins(id)')
  cols={row['name'] for row in db.execute('PRAGMA table_info(sessions)')}
  if 'last_seen' not in cols:db.execute('ALTER TABLE sessions ADD COLUMN last_seen REAL NOT NULL DEFAULT 0')
  db.execute("CREATE INDEX IF NOT EXISTS records_postal_scope ON records(kind,json_extract(body,'$.city_id'),coalesce(json_extract(body,'$.pincode'),json_extract(body,'$.postal_code'),json_extract(body,'$.inputs.pincode')))")
  centers=json.loads((CONFIG/'postal_centroids.json').read_text()) if (CONFIG/'postal_centroids.json').exists() else {'records':{}}
  for p in db.execute('SELECT * FROM pincodes').fetchall():
   ref=centers['records'].get(p['pincode'],{});lat=ref.get('latitude');lon=ref.get('longitude');source=ref.get('source')
   db.execute('INSERT OR IGNORE INTO admins(id,pincode,area_name,city_id,is_active,created_at,latitude,longitude,coordinate_source) VALUES (?,?,?,?,?,?,?,?,?)',(str(uuid4()),p['pincode'],p['locality_name'],p['city_id'],p['is_active'],now(),lat,lon,source))
   if lat is not None:db.execute('UPDATE admins SET latitude=coalesce(latitude,?),longitude=coalesce(longitude,?),coordinate_source=coalesce(coordinate_source,?) WHERE pincode=?',(lat,lon,source,p['pincode']))
  for old in db.execute('SELECT admin_id,pincode FROM admin_pincode_assignments').fetchall():
   new=db.execute('SELECT id FROM admins WHERE pincode=?',(old['pincode'],)).fetchone()
   if new:db.execute('INSERT OR IGNORE INTO area_assignment_migration VALUES (?,?,?)',(old['admin_id'],old['pincode'],new['id']))
  if not db.execute('SELECT 1 FROM schema_migrations WHERE version=2').fetchone():
   # Exact, unambiguous locality matching only; never infer a postal boundary from proximity.
   registry=[dict(p) for p in db.execute('SELECT * FROM pincodes')]
   for row in db.execute('SELECT id,kind,body FROM records').fetchall():
    item=json.loads(row['body']);pin=item.get('pincode') or item.get('postal_code') or item.get('inputs',{}).get('pincode')
    valid=next((p for p in registry if p['pincode']==pin and p['city_id']==item.get('city_id')),None)
    if not valid:
     location=str(item.get('location') or item.get('area') or item.get('locality') or '').strip().casefold()
     matches=[p for p in registry if p['city_id']==item.get('city_id') and location and location in [n.strip().casefold() for n in p['locality_name'].split(',')]]
     if len(matches)==1:valid=matches[0]
    item['pincode']=valid['pincode'] if valid else None;item['jurisdiction_status']='assigned' if valid else 'unassigned'
    db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(item,allow_nan=False),row['id']))
   for row in db.execute('SELECT id,kind,body FROM records').fetchall():
    item=json.loads(row['body'])
    if item.get('scenario_id') and not item.get('pincode'):
     parent=db.execute('SELECT body FROM records WHERE id=?',(item['scenario_id'],)).fetchone()
     if parent:
      data=json.loads(parent['body'])
      if data.get('pincode'):item.update(pincode=data['pincode'],city_id=data.get('city_id'),jurisdiction_status='assigned')
    if row['kind']=='complaint' and item.get('pincode'):
     administrator=db.execute('SELECT id FROM admins WHERE pincode=? AND is_active=1',(item['pincode'],)).fetchone()
     item['assigned_admin_id']=administrator['id'] if administrator else None
     db.execute('UPDATE complaint_jurisdictions SET area_admin_id=? WHERE complaint_id=?',(item['assigned_admin_id'],item['id']))
    db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(item,allow_nan=False),row['id']))
   db.execute('DELETE FROM sessions')
   db.execute('INSERT INTO schema_migrations VALUES (2,?)',(now(),))

  # Upgrade routing metadata without replacing historical identity rows.
  if not db.execute('SELECT 1 FROM schema_migrations WHERE version=3').fetchone():
   for row in db.execute("SELECT id,body FROM records WHERE kind='complaint'").fetchall():
    item=json.loads(row['body']);pin=item.get('pincode') or item.get('postal_code')
    administrator=db.execute('SELECT id FROM admins WHERE pincode=? AND city_id=? AND is_active=1',(pin,item.get('city_id'))).fetchone()
    if not administrator:continue
    item['assigned_admin_id']=administrator['id']
    db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(item,allow_nan=False),row['id']))
    db.execute('UPDATE complaint_jurisdictions SET area_admin_id=? WHERE complaint_id=?',(administrator['id'],row['id']))
   db.execute('INSERT INTO schema_migrations VALUES (3,?)',(now(),))
