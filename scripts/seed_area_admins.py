"""Seed official listed areas; no random PIN or additional secret is created."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.db.repository import initialize
from backend.db.connection import connection
initialize()
with connection() as db:
 for row in db.execute('SELECT pincode,area_name,is_active FROM admins ORDER BY pincode'):
  print(row['pincode']+' · '+row['area_name']+' · '+('active' if row['is_active'] else 'inactive'))
