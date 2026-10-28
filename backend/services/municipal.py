"""Postal routing and active local notices, without inventing municipal boundaries."""
import json
from backend.db.connection import connection
from backend.db import repository as repo
from backend.services.civic_service import verify_pin,context,active


def route_report(item):
    pin=item['postal_code'];verify_pin(item['city_id'],pin)
    with connection() as db:
        rows=db.execute('SELECT id,area_name AS display_name FROM admins WHERE pincode=? AND is_active=1 ORDER BY id',(pin,)).fetchall()
        assigned=rows[0]['id'] if rows else None
        db.execute('INSERT OR REPLACE INTO complaint_jurisdictions(complaint_id,pincode,city_id,assigned_admin_id) VALUES (?,?,?,?)',(item['id'],pin,item['city_id'],None))
        db.execute('UPDATE complaint_jurisdictions SET area_admin_id=? WHERE complaint_id=?',(assigned,item['id']))
        # The source report remains in records; the indexed relation adds no duplicate complaint.
        item['assigned_admin_id']=assigned;item['routing_status']='assigned_for_review' if assigned else 'awaiting_jurisdiction_assignment'
        db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(item,allow_nan=False),item['id']))
        db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(repo.now(),'postal_router','report_routed',item['id'],json.dumps({'pincode':pin,'assigned':bool(assigned)})))


def local_context(city_id,pin=None):
    if pin:verify_pin(city_id,pin)
    from backend.scope import current
    if current():pin=current()['pincode']
    c=context(city_id)
    with connection() as db:verified_authors={r['id'] for r in db.execute('SELECT id FROM admin_users WHERE is_active=1')} | {r['id'] for r in db.execute('SELECT id FROM admins WHERE is_active=1')}
    legacy_unverified={n['id'] for n in repo.all_records('civic_notice') if n.get('author_id') not in verified_authors}
    notices=[n for n in c['notices'] if n['id'] not in legacy_unverified and (not n.get('pincode') or n.get('pincode')==pin)]
    keys=('id','headline','area','description','publisher','source_url','valid_from','valid_until','pincode','kind','created','updated_at')
    notices=[{k:n.get(k) for k in keys} for n in notices if n.get('status','published')=='published']
    from backend.api.civic import public_report
    incidents=[public_report(n) for n in repo.all_records('complaint') if n['city_id']==city_id and n.get('validation')=='valid' and n['status']!='closed' and (not pin or n.get('postal_code')==pin)]
    return {'city_id':city_id,'pincode':pin,'notices':notices,'reviewed_incidents':incidents,'checked_at':repo.now(),
       'coverage_note':'Only reviewed incidents and active imported/platform notices. Missing reports or provider coverage do not establish low risk.'}


def save_report(body,fingerprint):
    """Claim submission and postal routing in the same write transaction."""
    import time
    from uuid import uuid4
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        previous=db.execute('SELECT report_id FROM report_deduplication WHERE key=? AND created>?',(fingerprint,time.time()-600)).fetchone()
        if previous:
            row=db.execute("SELECT body FROM records WHERE id=? AND kind='complaint'",(previous['report_id'],)).fetchone()
            if row:return json.loads(row['body'])
        pin=body['postal_code']
        if not db.execute('SELECT 1 FROM pincodes WHERE pincode=? AND city_id=? AND is_active=1',(pin,body['city_id'])).fetchone():
            from fastapi import HTTPException
            raise HTTPException(422,'PIN is not registered for the selected city')
        assigned=db.execute('SELECT id AS admin_id FROM admins WHERE pincode=? AND is_active=1',(pin,)).fetchone()
        administrator=assigned['admin_id'] if assigned else None
        item={**body,'pincode':pin,'id':str(uuid4()),'created':repo.now(),'assigned_admin_id':administrator,'routing_status':'assigned_for_review' if administrator else 'awaiting_jurisdiction_assignment'}
        db.execute('INSERT INTO records VALUES (?,?,?,?)',(item['id'],'complaint',item['created'],json.dumps(item,allow_nan=False)))
        db.execute('INSERT INTO complaint_jurisdictions(complaint_id,pincode,city_id,assigned_admin_id) VALUES (?,?,?,?)',(item['id'],pin,item['city_id'],None))
        db.execute('UPDATE complaint_jurisdictions SET area_admin_id=? WHERE complaint_id=?',(administrator,item['id']))
        db.execute('INSERT INTO report_deduplication VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET report_id=excluded.report_id,created=excluded.created',(fingerprint,item['id'],time.time()))
        db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(repo.now(),'civilian','report_submitted_and_routed',item['id'],json.dumps({'pincode':pin,'assigned':bool(administrator)})))
        return item
