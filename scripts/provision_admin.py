"""Manage a listed postal area from the trusted server console, without new secrets."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.db.repository import initialize,now
from backend.db.connection import connection
parser=argparse.ArgumentParser()
parser.add_argument('--pin',required=True);parser.add_argument('--deactivate',action='store_true');args=parser.parse_args()
initialize()
with connection() as db:
 row=db.execute('SELECT id FROM admins WHERE pincode=?',(args.pin,)).fetchone()
 if not row:parser.error('Unknown postal PIN. Add a sourced postal reference before seeding.')
 db.execute('UPDATE admins SET is_active=? WHERE pincode=?',(not args.deactivate,args.pin))
 db.execute('DELETE FROM sessions WHERE actor=?',('area:'+row['id'],))
 db.execute('INSERT INTO audit(created,actor,event,entity,detail) VALUES (?,?,?,?,?)',(now(),'trusted_console','area_assignment_changed',row['id'],'Area active state changed; sessions revoked'))
print('Area',args.pin,'deactivated' if args.deactivate else 'active')
