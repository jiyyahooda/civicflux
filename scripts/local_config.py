"""Create private local configuration once; never overwrite user settings."""
from pathlib import Path
import secrets
ROOT = Path(__file__).resolve().parents[1]
path = ROOT / '.env'
if not path.exists():
    content = (ROOT / '.env.example').read_text(encoding='utf-8')
    content = content.replace('CIVICFLUX_ADMIN_PASSWORD=\n', 'CIVICFLUX_ADMIN_PASSWORD=' + secrets.token_urlsafe(24) + '\n')
    with path.open('x', encoding='utf-8') as stream:
        stream.write(content)
    path.chmod(0o600)
    print('Created private .env. Read it locally for your administrator password.')
else:
    print('Existing .env preserved.')
