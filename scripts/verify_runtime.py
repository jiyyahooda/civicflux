"""Refresh inference evidence on either OS, without training or modifying models."""
from pathlib import Path
import json
import platform
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.civicflux.serving import discover
out = ROOT / 'reports/integration'
out.mkdir(parents=True, exist_ok=True)
failed = False
for entry in discover(ROOT):
    component = entry['component']
    target = out / (component + '.json')
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/check_research_inference.py'), component, '--output', str(target)], cwd=ROOT)
    failed |= result.returncode != 0
    if target.exists() and result.returncode == 0:
        report = json.loads(target.read_text(encoding='utf-8'))
        report['python'] = 'python' + platform.python_version()
        report['platform'] = platform.system() + ' ' + platform.machine()
        target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        # Existing legacy tests prefer this directory when a delivered archive has it.
        legacy = ROOT / 'reports/windows/inference'
        if legacy.exists():
            (legacy / target.name).write_text(target.read_text(encoding='utf-8'), encoding='utf-8')
sys.exit(1 if failed else 0)
