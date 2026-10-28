"""Complaint-only Gmail receipts. No general-purpose mail endpoint."""
import hashlib
import html
import logging
import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from backend.db.connection import connection
log=logging.getLogger(__name__)

def initialize():
 with connection() as db:
  db.executescript("""CREATE TABLE IF NOT EXISTS complaint_mail(report_id TEXT PRIMARY KEY,status TEXT NOT NULL,updated REAL NOT NULL);
  CREATE TABLE IF NOT EXISTS complaint_mail_limits(key TEXT NOT NULL,at REAL NOT NULL);
  CREATE INDEX IF NOT EXISTS mail_limits_window ON complaint_mail_limits(key,at);""")

def transport(message):
 user=os.getenv('SMTP_USER','');password=os.getenv('SMTP_PASS','')
 if not user or not password:raise RuntimeError('SMTP is not configured')
 port=int(os.getenv('SMTP_PORT','465'))
 if port not in (465,587):raise ValueError('Unsupported SMTP port')
 if port==465:
  with smtplib.SMTP_SSL('smtp.gmail.com',port,timeout=10,context=ssl.create_default_context()) as smtp:
   smtp.login(user,password);smtp.send_message(message)
 else:
  with smtplib.SMTP('smtp.gmail.com',port,timeout=10) as smtp:
   smtp.ehlo();smtp.starttls(context=ssl.create_default_context());smtp.ehlo();smtp.login(user,password);smtp.send_message(message)

def confirmation(item,ip):
 recipient=item['email_private'];now=time.time()
 with connection() as db:
  db.execute('BEGIN IMMEDIATE')
  prior=db.execute('SELECT status FROM complaint_mail WHERE report_id=?',(item['id'],)).fetchone()
  if prior:return prior['status']
  db.execute('DELETE FROM complaint_mail_limits WHERE at<?',(now-3600,))
  keys=[hashlib.sha256(('ip:'+ip).encode()).hexdigest(),hashlib.sha256(('recipient:'+recipient.lower()).encode()).hexdigest()]
  limited=any(db.execute('SELECT count(*) FROM complaint_mail_limits WHERE key=? AND at>?',(key,now-3600)).fetchone()[0]>=limit for key,limit in zip(keys,(10,3)))
  status='rate_limited' if limited else 'sending'
  db.execute('INSERT INTO complaint_mail VALUES (?,?,?)',(item['id'],status,now))
  if limited:return status
  for key in keys:db.execute('INSERT INTO complaint_mail_limits VALUES (?,?)',(key,now))
 message=EmailMessage();message['From']=os.getenv('SMTP_USER','');message['To']=recipient
 message['Subject']='CivicFlux complaint registered - Tracking ID '+item['id']
 fields=[('Tracking ID',item['id']),('Category',item['category']),('Location',item['location']+' · '+item['postal_code']),('Summary',item['description'][:500]),('Submitted',item['created'])]
 instruction='Open CivicFlux, choose Report a problem, and enter your full Tracking ID under Track your report.'
 message.set_content('Your CivicFlux complaint has been registered.\n\n'+'\n'.join(k+': '+str(v) for k,v in fields)+'\n\n'+instruction)
 message.add_alternative('<html><body><h1>Complaint registered</h1>'+''.join('<p><strong>'+html.escape(k)+'</strong><br>'+html.escape(str(v))+'</p>' for k,v in fields)+'<p>'+html.escape(instruction)+'</p></body></html>',subtype='html')
 try:transport(message);status='sent'
 except Exception as error:
  status='failed';log.warning('Complaint confirmation failed (%s); tracking ID %s',type(error).__name__,item['id'])
 with connection() as db:db.execute('UPDATE complaint_mail SET status=?,updated=? WHERE report_id=?',(status,time.time(),item['id']))
 return status
