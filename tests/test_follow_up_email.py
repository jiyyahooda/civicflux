import logging
import smtplib
import ssl
import pytest
from backend.services import complaint_email as mail
from backend.services.complaint_email import transport as smtp_transport

ISSUE={'report_id':'CF-2026-100','title':'Blocked drain','description':'Water is accumulating near the market.','category':'drainage','location':'Test locality','postal_code':'110001'}

@pytest.fixture(autouse=True)
def sender(monkeypatch):
 monkeypatch.setenv('SENDER_EMAIL','civicflux10@gmail.com')
 monkeypatch.setenv('SENDER_PASSWORD','test-only-app-password')
 monkeypatch.delenv('SMTP_HOST',raising=False)
 monkeypatch.delenv('SMTP_SECURITY',raising=False)
 monkeypatch.setenv('SMTP_PORT','465')

@pytest.mark.parametrize('security,port',[('ssl','465'),('starttls','587'),('starttls','2525')])
def test_transport_encrypts_before_login_and_uses_environment(monkeypatch,security,port):
 events=[]
 class SMTP:
  def __init__(self,host,port,**kw):
   assert host=='smtp.example.org' and port==int(os_port)
   if security=='ssl':assert kw['context'].verify_mode==ssl.CERT_REQUIRED and kw['context'].check_hostname
   events.append('connect')
  def __enter__(self):return self
  def __exit__(self,*args):events.append('close')
  def ehlo(self):events.append('ehlo')
  def starttls(self,context):
   assert context.verify_mode==ssl.CERT_REQUIRED and context.check_hostname
   events.append('tls')
  def login(self,user,password):
   assert user=='civicflux10@gmail.com' and password=='test-only-app-password'
   events.append('login')
  def send_message(self,message):events.append('send');return {}
 os_port=port
 monkeypatch.setenv('SMTP_HOST','smtp.example.org');monkeypatch.setenv('SMTP_PORT',port);monkeypatch.setenv('SMTP_SECURITY',security)
 monkeypatch.setattr(mail.smtplib,'SMTP_SSL',SMTP);monkeypatch.setattr(mail.smtplib,'SMTP',SMTP)
 smtp_transport(mail.build_follow_up('citizen@example.org',ISSUE))
 assert events==(['connect','login','send','close'] if security=='ssl' else ['connect','ehlo','tls','ehlo','login','send','close'])

def test_dynamic_issue_body_and_success_logging(monkeypatch,caplog):
 messages=[];monkeypatch.setattr(mail,'transport',messages.append)
 with caplog.at_level(logging.INFO,logger=mail.__name__):result=mail.send_follow_up('citizen@example.org',{**ISSUE,'description':'Issue <script>unsafe</script> & detail'})
 assert result=={'status':'sent','provider_accepted':True,'failure_code':None}
 m=messages[0];assert m['To']=='citizen@example.org' and m['From']=='civicflux10@gmail.com'
 assert ISSUE['report_id'] in m['Subject']
 assert 'review queue' in m.get_body(preferencelist=('plain',)).get_content()
 assert '&lt;script&gt;' in m.get_body(preferencelist=('html',)).get_content()
 assert 'accepted by SMTP server' in caplog.text
 assert 'citizen@example.org' not in caplog.text and 'unsafe' not in caplog.text

@pytest.mark.parametrize('error',[TimeoutError('secret recipient@example.org'),smtplib.SMTPAuthenticationError(535,b'secret password'),smtplib.SMTPRecipientsRefused({'secret@example.org':(550,b'private')})])
def test_failures_are_logged_without_sensitive_payloads(monkeypatch,caplog,error):
 def fail(message):raise error
 monkeypatch.setattr(mail,'transport',fail)
 with caplog.at_level(logging.WARNING,logger=mail.__name__):result=mail.send_follow_up('citizen@example.org',ISSUE)
 assert result['status']=='failed' and not result['provider_accepted']
 assert result['failure_code']==type(error).__name__
 assert 'failed' in caplog.text and 'secret' not in caplog.text and 'password' not in caplog.text

def test_refuse_plaintext_and_invalid_recipient(monkeypatch):
 monkeypatch.setenv('SMTP_SECURITY','none')
 with pytest.raises(ValueError):smtp_transport(mail.build_follow_up('citizen@example.org',ISSUE))
 assert mail.send_follow_up('bad\nBcc:other@example.org',ISSUE)['status']=='failed'

def test_legacy_environment_still_supported(monkeypatch):
 monkeypatch.delenv('SENDER_EMAIL');monkeypatch.delenv('SENDER_PASSWORD')
 monkeypatch.setenv('SMTP_USER','legacy@example.org')
 assert mail.build_follow_up('citizen@example.org',ISSUE)['From']=='legacy@example.org'
