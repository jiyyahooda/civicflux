import pytest
pytestmark=pytest.mark.usefixtures("civilian_account")
from pathlib import Path
from backend import config
from backend.db import repository as repo
from test_civic_workflows import report, image_bytes, login

def test_empty_browser_mime_is_decoded_and_report_is_trackable(client):
 body={'city_id':'delhi','title':'Photo upload regression','category':'drainage','location':'Disposable test locality','description':'A valid image with browser MIME omitted.','postal_code':'110001','email':'private@example.org'}
 response=client.post('/api/civic/reports',data=body,files=[('images',('issue.png',image_bytes(),'application/octet-stream'))])
 assert response.status_code==201,response.text
 item=response.json();assert item['id'] and item['status']=='submitted'
 assert client.get(item['images'][0]['url']).status_code==200
 public=client.get('/api/civic/reports/'+item['id']);assert public.status_code==200
 assert 'email_private' not in public.json() and 'internal_notes' not in public.json()
 assert client.get('/api/civic/reports/missing-id').status_code==404
 assert client.get('/api/civic/review?city_id=delhi').status_code==401
 login(client)
 assert any(r['id']==item['id'] for r in client.get('/api/civic/review?city_id=delhi').json())
 review={'validation':'valid','status':'under_review','department':'Drainage','public_reply':'Inspection recorded for the test report.','internal_notes':'Private evidence'}
 assert client.post('/api/civic/review/'+item['id'],json=review).status_code==200
 reopened=client.get('/api/civic/reports/'+item['id']).json()
 assert reopened['status']=='under_review' and reopened['public_reply']==review['public_reply']
 assert 'Private evidence' not in str(reopened)

def test_photo_storage_failure_never_creates_a_successful_report(client,monkeypatch):
 original=Path.write_bytes
 def fail_photo(path,data):
  if path.parent.name=='uploads':
   original(path,data[:5])
   raise PermissionError('Simulated interrupted photo write')
  return original(path,data)
 monkeypatch.setattr(Path,'write_bytes',fail_photo)
 result=report(client)
 assert result.status_code==503 and 'photos' in result.json()['detail']
 assert not repo.all_records('complaint')
 assert not list((config.DB_PATH.parent/'uploads').glob('*'))

def test_disguised_or_missing_images_remain_rejected(client):
 body={'city_id':'delhi','title':'Image validation','category':'road','location':'Disposable locality','description':'Regression photo validation.','postal_code':'110001','email':'private@example.org'}
 assert client.post('/api/civic/reports',data=body).status_code==422
 response=client.post('/api/civic/reports',data=body,files=[('images',('fake.png',b'not an image','application/octet-stream'))])
 assert response.status_code==422
 assert not repo.all_records('complaint')
