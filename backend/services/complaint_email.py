"""Secure SMTP support-form receipts. No general-purpose public mail endpoint."""
import hashlib
import html
import logging
import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from email_validator import validate_email, EmailNotValidError
from backend.db.connection import connection
log=logging.getLogger(__name__)

def initialize():
 with connection() as db:
  db.executescript("""CREATE TABLE IF NOT EXISTS complaint_mail(report_id TEXT PRIMARY KEY,status TEXT NOT NULL,updated REAL NOT NULL);
  CREATE TABLE IF NOT EXISTS complaint_mail_limits(key TEXT NOT NULL,at REAL NOT NULL);
  CREATE INDEX IF NOT EXISTS mail_limits_window ON complaint_mail_limits(key,at);""")
  cols={r['name'] for r in db.execute('PRAGMA table_info(complaint_mail)')}
  for name,typ in [('attempt_count','INTEGER NOT NULL DEFAULT 0'),('provider_accepted','INTEGER NOT NULL DEFAULT 0'),('failure_code','TEXT')]:
   if name not in cols:db.execute('ALTER TABLE complaint_mail ADD COLUMN '+name+' '+typ)

def sender_email():
 return os.getenv('SENDER_EMAIL') or os.getenv('SMTP_USER','')

def transport(message):
 """Use verified SSL or STARTTLS; authenticate only after encryption is active."""
 user=sender_email();password=os.getenv('SENDER_PASSWORD') or os.getenv('SMTP_PASS','')
 if not user or not password:raise RuntimeError('SMTP sender credentials are not configured')
 host=os.getenv('SMTP_HOST','smtp.gmail.com').strip()
 port=int(os.getenv('SMTP_PORT','465'))
 security=os.getenv('SMTP_SECURITY','ssl' if port==465 else 'starttls').lower()
 timeout=float(os.getenv('SMTP_TIMEOUT','10'))
 if not host or any(c in host for c in '\r\n') or not 1<=port<=65535 or not 0<timeout<=120:raise ValueError('Invalid SMTP configuration')
 if security not in {'ssl','starttls'}:raise ValueError('SMTP_SECURITY must be ssl or starttls; plaintext is not supported')
 context=ssl.create_default_context()
 if security=='ssl':
  with smtplib.SMTP_SSL(host,port,timeout=timeout,context=context) as smtp:
   smtp.login(user,password)
   refused=smtp.send_message(message)
   if refused:raise smtplib.SMTPRecipientsRefused(refused)
 else:
  with smtplib.SMTP(host,port,timeout=timeout) as smtp:
   smtp.ehlo();smtp.starttls(context=context);smtp.ehlo();smtp.login(user,password)
   refused=smtp.send_message(message)
   if refused:raise smtplib.SMTPRecipientsRefused(refused)

def build_follow_up(recipient_email, issue_details):
 """Build plain-text and escaped HTML versions using dynamic report details."""
 try:
  recipient=validate_email(recipient_email,check_deliverability=False).normalized
  sender=validate_email(sender_email(),check_deliverability=False).normalized
 except EmailNotValidError:raise ValueError('Invalid sender or recipient email address') from None
 if not isinstance(issue_details,dict):raise ValueError('issue_details must be a dictionary')
 reference=str(issue_details.get('report_id') or issue_details.get('id') or '').strip()
 description=str(issue_details.get('description') or '').strip()
 if not reference or len(reference)>160 or any(c in reference for c in '\r\n') or not description:raise ValueError('A report ID and issue description are required')
 message=EmailMessage();message['From']=sender;message['To']=recipient
 message['Subject']='CivicFlux report registered - Tracking ID '+reference
 fields=[('Title',issue_details.get('title','CivicFlux report')),('City',issue_details.get('city_id','Not specified')),('Status',issue_details.get('status','submitted')),('Tracking ID',reference),('Category',issue_details.get('category','Not specified')),('Location',str(issue_details.get('location','Not specified'))+' · '+str(issue_details.get('postal_code',''))),('Summary',description),('Submitted',issue_details.get('created','Not specified'))]
 introduction='Thank you for contacting CivicFlux. We have received your reported issue and added it to our review queue. Our team will review the information and update your report as it progresses.'
 instruction='Open CivicFlux, choose Report a problem, and enter your full Tracking ID under Track your report.'
 disclaimer='This is a report registered in CivicFlux. It has not been submitted to a government complaint system.'
 closing='Thank you for helping improve your community.\nCivicFlux Support'
 message.set_content(introduction+'\n\n'+'\n'.join(k+': '+str(v) for k,v in fields)+'\n\n'+instruction+'\n\n'+disclaimer+'\n\n'+closing)
 message.add_alternative('<html><body><h1>We have received your report</h1><p>'+html.escape(introduction)+'</p>'+''.join('<p><strong>'+html.escape(k)+'</strong><br>'+html.escape(str(v))+'</p>' for k,v in fields)+'<p>'+html.escape(instruction)+'</p><p>'+html.escape(disclaimer)+'</p><p>Thank you for helping improve your community.<br>CivicFlux Support</p></body></html>',subtype='html')
 return message

def send_follow_up(recipient_email, issue_details):
 """Send a support receipt; returns SMTP acceptance, not confirmed inbox delivery.

 Credentials are read on each call. This function performs no automatic retries:
 a network timeout after sending can leave delivery uncertain.
 """
 reference=hashlib.sha256(str(issue_details.get('report_id',issue_details.get('id','')) if isinstance(issue_details,dict) else '').encode()).hexdigest()[:12]
 try:
  transport(build_follow_up(recipient_email,issue_details))
  log.info('Support follow-up accepted by SMTP server; reference=%s',reference)
  return {'status':'sent','provider_accepted':True,'failure_code':None}
 except Exception as error:
  kind='authentication' if isinstance(error,smtplib.SMTPAuthenticationError) else 'smtp' if isinstance(error,smtplib.SMTPException) else 'network' if isinstance(error,OSError) else 'configuration_or_input'
  # Do not log exceptions, addresses, credentials or issue bodies: SMTP replies can contain them.
  failure=type(error).__name__
  log.warning('Support follow-up failed; kind=%s error_type=%s reference=%s',kind,failure,reference)
  return {'status':'failed','provider_accepted':False,'failure_code':failure}

def confirmation(item,ip):
 recipient=item['email_private'];now=time.time()
 with connection() as db:
  db.execute('BEGIN IMMEDIATE')
  prior=db.execute('SELECT status FROM complaint_mail WHERE report_id=?',(item['id'],)).fetchone()
  if prior:return prior['status']
  db.execute('DELETE FROM complaint_mail_limits WHERE at<?',(now-3600,))
  keys=[hashlib.sha256(('ip:'+ip).encode()).hexdigest(),hashlib.sha256(('recipient:'+recipient.lower()).encode()).hexdigest()]
  limited=any(db.execute('SELECT count(*) FROM complaint_mail_limits WHERE key=? AND at>?',(key,now-3600)).fetchone()[0]>=limit for key,limit in zip(keys,(10,3)))
  status='rate_limited' if limited else 'queued'
  db.execute('INSERT INTO complaint_mail(report_id,status,updated) VALUES (?,?,?)',(item['id'],status,now))
  if limited:return status
  for key in keys:db.execute('INSERT INTO complaint_mail_limits VALUES (?,?)',(key,now))
 failure=None
 try:
  with connection() as db:db.execute("UPDATE complaint_mail SET status='sending',attempt_count=attempt_count+1,updated=? WHERE report_id=?",(time.time(),item['id']))
  message=build_follow_up(recipient,item)
  transport(message);status='sent'
  log.info('Complaint confirmation accepted by SMTP server; tracking ID %s',item['id'])
 except Exception as error:
  status='failed';failure=type(error).__name__;log.warning('Complaint confirmation failed (%s); tracking ID %s',failure,item['id'])
 with connection() as db:db.execute('UPDATE complaint_mail SET status=?,updated=?,provider_accepted=?,failure_code=? WHERE report_id=?',(status,time.time(),int(status=='sent'),failure,item['id']))
 return status
