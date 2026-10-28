"""Create local credentials once; preserve existing administrator/provider settings."""
from pathlib import Path
import secrets
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'.env'
if not path.exists():
    text=(ROOT/'.env.example').read_text(encoding='utf-8')
    text=text.replace('CIVICFLUX_ADMIN_PASSWORD=\n','CIVICFLUX_ADMIN_PASSWORD='+secrets.token_urlsafe(24)+'\n')
    with path.open('x',encoding='utf-8') as stream:stream.write(text)
    path.chmod(0o600)
    print('Created local configuration. Read .env privately for the initial supervisor login.')
else:print('Existing local configuration preserved. Administrator passwords are stored as hashes in the database.')
