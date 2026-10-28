"""Provision or update a scoped administrator without putting passwords in arguments."""
import argparse,getpass,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.db.repository import initialize
from backend.services.administration import provision
parser=argparse.ArgumentParser()
parser.add_argument('--username',required=True);parser.add_argument('--display-name',required=True)
parser.add_argument('--role',choices=['officer','city_supervisor','system_supervisor'],default='officer')
parser.add_argument('--pin',action='append',default=[]);parser.add_argument('--city',action='append',default=[])
args=parser.parse_args();initialize()
password=os.getenv('CIVICFLUX_NEW_ADMIN_PASSWORD') or getpass.getpass('Administrator password (not a postal PIN): ')
result=provision(args.username,password,args.display_name,args.role,args.pin,args.city)
print('Provisioned',result['username'],'with',len(result['assignments']),'PIN assignments. Password not displayed.')
