"""Expose a bounded, credential-free Docker build error in public CI annotations."""
from pathlib import Path
import sys
message = '\n'.join(Path(sys.argv[1]).read_text().splitlines()[-55:])
message = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
print('::error title=Container build failure::' + message)
