from test_api_scenarios import run
from backend import config

def test_reviews_never_approve_and_verification_is_separate(admin_client):
    item=run(admin_client);base='/api/feedback/'+item['id']
    assert admin_client.post(base+'/review',json={'decision':'approve','note':'Request approval'}).status_code==409
    review=admin_client.post(base+'/review',json={'decision':'defer','note':'Needs a field inspection'})
    assert review.status_code==200
    assert review.json()['dispatch_allowed'] is False
    saved=admin_client.get('/api/scenarios/'+item['id']).json()
    assert saved['review_status']=='deferred' and saved['dispatch_allowed'] is False
    assert saved['latest_review_id']==review.json()['id']
    from datetime import datetime,timezone
    body={'verifier':'external-auditor','evidence_ref':'simulation-log-100','success':True,'completion_time':item['created'],'verification_time':datetime.now(timezone.utc).isoformat(),'note':'Independent simulation log review'}
    response=admin_client.post(base+'/verification',json=body)
    assert response.status_code==200,response.text
    assert response.json()['real_outcome_verified'] is False
    data=admin_client.get('/api/feedback').json()
    assert len(data['reviews'])==1 and len(data['verifications'])==1
    body['verifier']=review.json()['reviewer']
    assert admin_client.post(base+'/verification',json=body).status_code==422
    body['verification_time']='2025-01-01T00:00:00Z'
    assert admin_client.post(base+'/verification',json=body).status_code==422

def test_civilian_complaint_and_admin_transitions(client):
    body={'city_id':'delhi','category':'drainage','location':'Community park entrance','description':'The drain appears blocked after rain.'}
    from test_civic_workflows import report
    item=report(client)
    assert item.status_code==201
    identifier=item.json()['id']
    assert client.post('/api/complaints/'+identifier,json={'status':'under_review','note':'Checking the report'}).status_code==401
    assert client.post('/api/auth/login',json={'username':config.ADMIN_ID,'password':config.ADMIN_PASSWORD}).status_code==200
    assert client.post('/api/complaints/'+identifier,json={'status':'closed','note':'Skip review'}).status_code==409
    assert client.post('/api/complaints/'+identifier,json={'status':'under_review','note':'Inspection requested'}).status_code==200
    assert client.get('/api/audit').json()
    client.post('/api/auth/logout')
    assert client.get('/api/audit').status_code==401

def test_bad_login_and_cross_origin_admin_write(client):
    assert client.post('/api/auth/login',json={'username':'admin','password':'wrong'}).status_code==401
    assert client.post('/api/auth/login',json={'username':config.ADMIN_ID,'password':config.ADMIN_PASSWORD}).status_code==200
    assert client.post('/api/scenarios',json={},headers={'Origin':'https://another.example'}).status_code==403
