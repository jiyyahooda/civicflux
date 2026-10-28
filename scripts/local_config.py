"""Create provider configuration once; area logins use existing public postal PINs."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'.env'
if not path.exists():
    with path.open('x',encoding='utf-8') as stream:stream.write((ROOT/'.env.example').read_text(encoding='utf-8'))
    path.chmod(0o600)
    print('Created private provider configuration. Area login: admin + six-digit listed postal PIN.')
else:print('Existing provider configuration preserved. Area login: admin + six-digit listed postal PIN.')
