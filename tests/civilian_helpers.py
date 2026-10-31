"""Test-only provider stub; exercise the real challenge and session flow."""
SENT={}
def sign_in(client,phone='9000000001'):
 existing=client.get('/api/civilian/session').json()['user']
 if existing and existing['phone']==phone:return existing
 r=client.post('/api/civilian/otp/send',json={'name':'Test Citizen','phone':phone});assert r.status_code==200,r.text
 response=client.post('/api/civilian/otp/verify',json={'challenge_id':r.json()['challenge_id'],'otp':SENT[phone]});assert response.status_code==200,response.text
 return response.json()['user']
