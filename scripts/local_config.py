"""Create local settings and apply the owner's shared development login."""
from pathlib import Path
from dotenv import set_key

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / '.env'
if not path.exists():
    with path.open('x', encoding='utf-8') as stream:
        stream.write((ROOT / '.env.example').read_text(encoding='utf-8'))
# All project contributors currently use the same owner-requested local login.
# Preserve API keys, database paths and other machine-specific configuration.
set_key(str(path), 'CIVICFLUX_ADMIN_ID', 'admin')
set_key(str(path), 'CIVICFLUX_ADMIN_PASSWORD', '001')
path.chmod(0o600)
print('Local configuration ready. Admin ID: admin | Password: 001')
