"""Additive municipal schema; existing record IDs, uploads and history are retained."""
import json
import re
from datetime import datetime,timezone
from pathlib import Path
from backend.db.connection import connection
from project_paths import CONFIG
SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS auth_attempts(key TEXT PRIMARY KEY, failures INTEGER NOT NULL, last_attempt REAL NOT NULL);
CREATE TABLE IF NOT EXISTS cities(id TEXT PRIMARY KEY, name TEXT NOT NULL, state_or_ut TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS pincodes(
 pincode VARCHAR(6) PRIMARY KEY CHECK(length(pincode)=6), city_id TEXT NOT NULL REFERENCES cities(id),
 locality_name TEXT NOT NULL, district_name TEXT, state_or_ut TEXT NOT NULL,
 latitude REAL, longitude REAL, source TEXT NOT NULL, source_updated_at TEXT NOT NULL,
 is_active INTEGER NOT NULL DEFAULT 1, jurisdiction_note TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS admin_users(
 id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 display_name TEXT NOT NULL, role TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL, last_login_at TEXT, government_verified INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS admin_city_assignments(
 admin_id TEXT NOT NULL REFERENCES admin_users(id), city_id TEXT NOT NULL REFERENCES cities(id),
 PRIMARY KEY(admin_id,city_id));
CREATE TABLE IF NOT EXISTS admin_pincode_assignments(
 admin_id TEXT NOT NULL REFERENCES admin_users(id), pincode TEXT NOT NULL REFERENCES pincodes(pincode),
 assignment_role TEXT NOT NULL, assigned_at TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1,
 PRIMARY KEY(admin_id,pincode));
CREATE TABLE IF NOT EXISTS complaint_jurisdictions(
 complaint_id TEXT PRIMARY KEY REFERENCES records(id), pincode TEXT NOT NULL REFERENCES pincodes(pincode),
 city_id TEXT NOT NULL REFERENCES cities(id), assigned_admin_id TEXT REFERENCES admin_users(id));
CREATE TABLE IF NOT EXISTS locality_budgets(
 id TEXT PRIMARY KEY, city_id TEXT NOT NULL REFERENCES cities(id), pincode TEXT NOT NULL REFERENCES pincodes(pincode),
 pool_id TEXT NOT NULL REFERENCES resource_pools(id), budget INTEGER NOT NULL CHECK(budget>=0),
 severity_weight REAL NOT NULL DEFAULT .6, population_weight REAL NOT NULL DEFAULT .4,
 fiscal_year TEXT NOT NULL, source_ref TEXT NOT NULL, created_by TEXT NOT NULL,
 created_at TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS report_deduplication(key TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES records(id), created REAL NOT NULL);
CREATE TRIGGER IF NOT EXISTS complaint_city_pin_insert BEFORE INSERT ON complaint_jurisdictions
WHEN NOT EXISTS(SELECT 1 FROM pincodes WHERE pincode=NEW.pincode AND city_id=NEW.city_id)
BEGIN SELECT RAISE(ABORT,'Complaint city and PIN do not match'); END;
CREATE TRIGGER IF NOT EXISTS complaint_city_pin_update BEFORE UPDATE OF pincode,city_id ON complaint_jurisdictions
WHEN NOT EXISTS(SELECT 1 FROM pincodes WHERE pincode=NEW.pincode AND city_id=NEW.city_id)
BEGIN SELECT RAISE(ABORT,'Complaint city and PIN do not match'); END;
CREATE TRIGGER IF NOT EXISTS locality_budget_city_pin_insert BEFORE INSERT ON locality_budgets
WHEN NOT EXISTS(SELECT 1 FROM pincodes WHERE pincode=NEW.pincode AND city_id=NEW.city_id)
BEGIN SELECT RAISE(ABORT,'Budget city and PIN do not match'); END;
CREATE INDEX IF NOT EXISTS pincodes_city ON pincodes(city_id,is_active);
CREATE INDEX IF NOT EXISTS assignment_pin ON admin_pincode_assignments(pincode,is_active);
CREATE VIEW IF NOT EXISTS complaints AS SELECT id,created AS created_at,
 json_extract(body,'$.city_id') city_id,json_extract(body,'$.postal_code') pincode,
 json_extract(body,'$.title') title,json_extract(body,'$.description') description,
 json_extract(body,'$.category') category,json_extract(body,'$.status') status,
 json_extract(body,'$.location') reported_address,json_extract(body,'$.email_private') reporter_email,
 json_extract(body,'$.reported_damage_priority') citizen_damage_priority,
 json_extract(body,'$.reported_affected_people_count') citizen_affected_people_count,
 json_extract(body,'$.damage_priority') officer_damage_priority,
 json_extract(body,'$.affected_people_count') officer_affected_people_count,
 json_extract(body,'$.assigned_admin_id') assigned_admin_id,
 json_extract(body,'$.department') assigned_department,json_extract(body,'$.public_reply') admin_response,
 json_extract(body,'$.images') image_reference,json_extract(body,'$.coordinates') coordinates,
 json_extract(body,'$.updated_at') updated_at,json_extract(body,'$.verified_at') verified_at
 FROM records WHERE kind='complaint';
CREATE VIEW IF NOT EXISTS notices AS SELECT id,created AS created_at,
 json_extract(body,'$.city_id') city_id,json_extract(body,'$.pincode') pincode,
 json_extract(body,'$.headline') title,json_extract(body,'$.description') message,
 json_extract(body,'$.publisher') author_role,json_extract(body,'$.author_id') author_id,
 json_extract(body,'$.source_url') source_url,json_extract(body,'$.valid_from') valid_from,
 json_extract(body,'$.valid_until') valid_until,json_extract(body,'$.status') status,
 json_extract(body,'$.updated_at') updated_at FROM records WHERE kind='civic_notice';
"""

def migrate():
    from backend.services.city_service import cities
    stamp=datetime.now(timezone.utc).isoformat()
    reference=json.loads((CONFIG/'postal_reference.json').read_text(encoding='utf-8'))
    states={'delhi':'Delhi','chandigarh':'Chandigarh','chennai':'Tamil Nadu'}
    with connection() as db:
        db.executescript(SQL)
        for c in cities():db.execute('INSERT OR IGNORE INTO cities VALUES (?,?,?)',(c['id'],c['name'],states[c['id']]))
        for cid,block in reference.items():
            grouped={}
            for row in block['records']:
                pin=row['pin']
                if not isinstance(pin,str) or not re.fullmatch('[1-9][0-9]{5}',pin):raise ValueError('Invalid reference PIN')
                grouped.setdefault(pin,set()).add(row['area'])
            for pin,areas in grouped.items():
                old=db.execute('SELECT city_id FROM pincodes WHERE pincode=?',(pin,)).fetchone()
                if old and old['city_id']!=cid:raise ValueError('Conflicting city assignment in postal source')
                db.execute('INSERT OR IGNORE INTO pincodes VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                  (pin,cid,', '.join(sorted(areas)),None,states[cid],None,None,block['source_url'],block['retrieved_at'],1,'Postal reference only; PIN does not establish a ward or municipal boundary.'))
        for row in db.execute("SELECT id,body FROM records WHERE kind='complaint'").fetchall():
            body=json.loads(row['body']);pin=body.get('postal_code')
            if db.execute('SELECT 1 FROM pincodes WHERE pincode=? AND city_id=?',(pin,body.get('city_id'))).fetchone():
                db.execute('INSERT OR IGNORE INTO complaint_jurisdictions VALUES (?,?,?,NULL)',(row['id'],pin,body['city_id']))
        db.execute('INSERT OR IGNORE INTO schema_migrations VALUES (1,?)',(stamp,))
    from backend.services.administration import bootstrap
    bootstrap()
