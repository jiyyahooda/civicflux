import json
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from .connection import connection
from .schema import SQL

def now(): return datetime.now(timezone.utc).isoformat()

def initialize():
    with connection() as db: db.executescript(SQL)
    from backend.services.authority_service import authorities
    from backend.services.city_service import cities
    for configuration in cities():authorities(configuration['id'])
    from backend.api.resources import initialize as initialize_resources
    initialize_resources()
    from backend.db.municipal import migrate
    migrate()
    from backend.services.complaint_email import initialize as initialize_mail
    initialize_mail()
    from backend.db.areas import migrate as migrate_areas
    migrate_areas()

def append(kind, body, actor='civilian', event='created'):
    from backend.scope import bind
    body=bind(body)
    item = {**body, 'id':str(uuid4()), 'created':now()}
    with connection() as db:
        db.execute('INSERT INTO records VALUES (?,?,?,?)', (item['id'], kind, item['created'], json.dumps(item, allow_nan=False)))
        db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)', (now(),actor,event,item['id'],json.dumps({'kind':kind})))
    return item

def all_records(kind):
    with connection() as db:
        from backend.scope import current
        scope=current()
        if scope:return [json.loads(r['body']) for r in db.execute("SELECT body FROM records WHERE kind=? AND json_extract(body,'$.city_id')=? AND coalesce(json_extract(body,'$.pincode'),json_extract(body,'$.postal_code'),json_extract(body,'$.inputs.pincode'))=? ORDER BY created DESC",(kind,scope['city_id'],scope['pincode']))]
        return [json.loads(r['body']) for r in db.execute('SELECT body FROM records WHERE kind=? ORDER BY created DESC',(kind,))]

def record_scenario_review(identifier, body, actor):
    scenario_scope=get('scenario',identifier)
    from backend.scope import pin_of
    body={**body,'city_id':scenario_scope['city_id'],'pincode':pin_of(scenario_scope)}
    """Persist the review and visible scenario status atomically, never approval."""
    states={'pending':'pending','defer':'deferred','reject':'rejected'}
    if body['decision'] not in states or body.get('dispatch_allowed') is not False:
        raise ValueError('Research review cannot approve or dispatch')
    item={**body,'scenario_id':identifier,'id':str(uuid4()),'created':now()}
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT body FROM records WHERE kind='scenario' AND id=?",(identifier,)).fetchone()
        if row is None: raise HTTPException(404,'Scenario not found')
        scenario=json.loads(row['body'])
        scenario.update(review_status=states[body['decision']],latest_review_id=item['id'],dispatch_allowed=False)
        db.execute('INSERT INTO records VALUES (?,?,?,?)',(item['id'],'review',item['created'],json.dumps(item,allow_nan=False)))
        db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(scenario,allow_nan=False),identifier))
        db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',
                   (now(),actor,'human_review',item['id'],json.dumps({'kind':'review','scenario_id':identifier,'decision':body['decision']})))
    return item

def get(kind, identifier):
    with connection() as db: row=db.execute('SELECT body FROM records WHERE kind=? AND id=?',(kind,identifier)).fetchone()
    from backend.scope import allows
    if row is None or not allows(json.loads(row['body'])): raise HTTPException(404, 'Record not found')
    return json.loads(row['body'])

def update_complaint(identifier, status, note, actor):
    get('complaint',identifier)
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT body FROM records WHERE kind='complaint' AND id=?",(identifier,)).fetchone()
        if row is None: raise HTTPException(404,'Complaint not found')
        item=json.loads(row['body']); previous=item['status']
        transitions={'submitted':['under_review'], 'under_review':['in_progress','closed'], 'in_progress':['closed','under_review'], 'closed':['under_review']}
        if status not in transitions[previous]: raise HTTPException(409,'Invalid complaint transition')
        item['status']=status;item['history'].append({'status':status,'note':note,'actor':actor,'time':now()})
        db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(item),identifier))
        db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(now(),actor,'complaint_review',identifier,note))
    return item

def audit():
    with connection() as db: return [dict(r) for r in db.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 500')]

def route_complaint(identifier,locality,note,actor):
    get('complaint',identifier)
    from backend.services.authority_service import assign
    original=get('complaint',identifier)
    routing=assign(original['city_id'],locality)
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT body FROM records WHERE kind='complaint' AND id=?",(identifier,)).fetchone()
        if row is None:raise HTTPException(404,'Complaint not found')
        item=json.loads(row['body']);item.update(routing)
        item['history'].append({'status':item['status'],'note':'Routed to '+routing['authority_name']+': '+note,'actor':actor,'time':now()})
        db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(item),identifier))
        db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(now(),actor,'complaint_routed',identifier,json.dumps(routing)))
    return item


def revise(kind, identifier, changes, actor, event):
    get(kind,identifier)
    from backend.scope import bind
    changes=bind(changes)
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT body FROM records WHERE kind=? AND id=?',(kind,identifier)).fetchone()
        if row is None:raise HTTPException(404,'Record not found')
        item=json.loads(row['body']);item.update(changes);item['updated_at']=now()
        db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(item,allow_nan=False),identifier))
        db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(now(),actor,event,identifier,json.dumps({'kind':kind})))
    return item
