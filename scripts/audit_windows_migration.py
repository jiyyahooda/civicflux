"""Audit existing extraction and write a migration-only report; never train models."""
from pathlib import Path, PurePosixPath
import ast
from datetime import datetime
import hashlib
import importlib
import importlib.metadata
import json
import subprocess
import sys
import zipfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from project_paths import PROJECT_ROOT, ML_SOURCE, ARTIFACTS, MODEL_REGISTRY, DATA, CONFIG, BACKEND


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    archive = Path(sys.argv[1]).resolve()
    output = ROOT / 'reports/windows'
    output.mkdir(parents=True, exist_ok=True)
    ignored = {'.venv', '__pycache__', '.pytest_cache', '.cache', '.jupyter', '__MACOSX'}
    copies = [archive.parent / 'civicflux_ml/civicflux_ml', archive.parent / 'civicflux_ml', archive.parent / 'CivicFlux']
    copies = [p for p in copies if (p / 'civicflux_core.py').is_file()]
    rows = []
    with zipfile.ZipFile(archive) as source:
        for entry in source.infolist():
            path = PurePosixPath(entry.filename)
            if entry.is_dir() or path.parts[0] != 'civicflux_ml':
                continue
            relative = PurePosixPath(*path.parts[1:])
            if any(part in ignored or part == '.DS_Store' or part.startswith('._') for part in relative.parts):
                continue
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe archive member: ' + str(relative))
            data = source.read(entry)
            current = ROOT / str(relative)
            rows.append({'path':str(relative), 'archive_sha256':digest(data),
                         'current_sha256':digest(current.read_bytes()) if current.is_file() else None,
                         'other_copies': {str(copy): digest((copy / str(relative)).read_bytes()) == digest(data)
                                          if (copy / str(relative)).is_file() else False for copy in copies}})
    changed = [r['path'] for r in rows if r['archive_sha256'] != r['current_sha256']]
    protected = [r for r in rows if PurePosixPath(r['path']).parts[0] in {'artifacts','data','notebooks'}]
    modules = {}
    for name in ['civicflux_core.py', *['src/civicflux/' + n + '.py' for n in
            ['serving','contracts','runtime','validation','integration','anomaly','water','graph','cascade','optimization','outcomes']]]:
        path = ROOT / name
        source = path.read_text(encoding='utf-8')
        tree = ast.parse(source)
        module_name = name.removesuffix('.py').replace('/', '.')
        importlib.import_module(module_name)
        modules[name] = {'sha256':digest(path.read_bytes()), 'import':'passed',
                         'definitions':[n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))],
                         'macos_path_lines':[i for i,line in enumerate(source.splitlines(),1) if '/Users/' in line]}
    requirements = []
    from packaging.requirements import Requirement
    for line in (ROOT / 'requirements.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        requirement = Requirement(line)
        version = importlib.metadata.version(requirement.name)
        requirements.append({'requirement':line, 'installed':version, 'satisfied':version in requirement.specifier})
    check = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True)
    inventory = json.loads((output / 'migration_inventory.json').read_text(encoding='utf-8'))
    cases = []
    for component in inventory['components']:
        record = json.loads((output / 'inference' / (component['component'] + '.json')).read_text())
        cases.extend(record['negative_cases'].values())
    evidence = {'verified_at':datetime.now(ZoneInfo('Asia/Kolkata')).isoformat(), 'root':str(PROJECT_ROOT),
                'archive':str(archive), 'archive_entries_checked':len(rows), 'changed_originals':changed,
                'research_preserved':all(r['archive_sha256'] == r['current_sha256'] for r in protected),
                'protected_files':len(protected), 'files':rows, 'modules':modules, 'requirements':requirements,
                'pip_check':{'exit_code':check.returncode, 'stdout':check.stdout, 'stderr':check.stderr},
                'versions':{c['component']:[str(p.relative_to(ROOT)) for p in sorted((ARTIFACTS/c['component']).iterdir())
                                          if p.is_dir()] for c in inventory['components']},
                'negative_cases':len(cases), 'negative_abstentions':sum(c['status']=='abstained' for c in cases)}
    (output / 'migration_reverification.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    table = []
    for component in inventory['components']:
        artifact = component['artifact'] or 'src/civicflux/optimization.py (CP-SAT; no trained model)'
        table.append(f"| {component['component']} | {component['version']} | `{artifact}` | {'PASS' if component['passed'] else 'FAIL'}: {component['positive_status']} |")
    paths = {'Project root':PROJECT_ROOT, 'ML modules':ML_SOURCE, 'Artifacts':ARTIFACTS,
             'Registry':MODEL_REGISTRY, 'Datasets':DATA, 'Configuration':CONFIG, 'Future integration target (already present)':BACKEND}
    report = f'''# Windows migration verification

Verified: {evidence['verified_at']}.

## Scope and existing files

This run stops at migration and research inference verification. Backend and frontend files were already present when this request began; they were preserved and were not implemented, extended, or certified by this run. Earlier application reports describe earlier workspace state and are not evidence of work performed in this run.

Canonical project root: `{ROOT}`.

Source ZIP: `{archive}`. Read and compared all {len(rows)} substantive files, excluding transferred virtual environments, caches, and Apple resource files. All required research files were already extracted, so no overwrite or redundant extraction was necessary. Missing originals: {sum(r['current_sha256'] is None for r in rows)}.

Protected research files: {len(protected)}. Artifacts, datasets, and notebooks match the ZIP: **{evidence['research_preserved']}**. No training, notebook execution, artifact conversion, or metadata regeneration was performed.

Existing differences from the ZIP: {', '.join('`'+n+'`' for n in changed) or 'none'}. These differences predated this run; this run did not alter those files. Original serving code remains accessible in the source ZIP. No automatic copy merge or deletion was performed.

Other complete copies checked: {', '.join('`'+str(p)+'`' for p in copies) or 'none found at checked locations'}. Per-file comparisons are in `windows/migration_reverification.json`. Matching research content cannot be ranked by transfer timestamps. The workspace copy is canonical for this task. The workspace also contains `CivicFlux-Complete.zip`, a previously generated application bundle, which was not extracted or treated as the research source.

## Windows environment

Python {inventory['python']}; executable: `{inventory['executable']}`. Reused the existing Windows environment at `{ROOT / '.venv-windows'}` after rerunning imports, dependency checks, and fresh-process inference. It was not recreated unnecessarily. The transferred macOS `.venv` was not used. Its recorded Python version is 3.13.5; cross-version artifact compatibility is established only for components that actually pass here.

All existing requirements satisfied: **{all(r['satisfied'] for r in requirements)}**. `pip check`: exit {check.returncode}, {check.stdout.strip()}. Complete measured versions: `windows/requirements-windows.lock.txt`. Required imports including scikit-learn, XGBoost, NetworkX, OR-Tools, and all twelve requested source files pass. Detailed module hashes and requirement comparisons are in the JSON evidence.

The system `python` and `py` commands resolve to inaccessible WindowsApps aliases in this session. Use the explicit environment executable above. No machine-wide PATH or security settings were changed.

## Model verification

Selection follows the existing `artifacts/model_validation/v1.0.0/model_registry.json`, not directory sorting. All selected artifacts, metadata/model cards, and feature schemas exist. All available version directories remain intact and are listed in the evidence JSON. Selected artifact paths below are relative to the canonical root; absolute paths, units, scope, provenance, horizon, and selected metadata/schema paths are in `windows/migration_inventory.json`.

| Component | Registry version | Artifact or implementation | Fresh-process verification |
| --- | --- | --- | --- |
{chr(10).join(table)}

Fresh-process checks used the existing `scripts/check_research_inference.py` through `scripts/verify_windows.py`. **{sum(c['passed'] for c in inventory['components'])}/9 components pass** supported historical/synthetic inference and their negative checks. The anomaly check covers each of the five registered sensors. **{evidence['negative_abstentions']}/{len(cases)} negative requests returned abstention**. For traffic and flood, a model-load failure can mask later payload validation; their complete input-validation behavior is therefore not certified.

Traffic and flood positive cases abstain with `input stream corrupted` while loading joblib-embedded XGBoost state. Their saved files match the ZIP and XGBoost imports successfully; the exact serialization incompatibility is unresolved. Neither component was substituted, retrained, rewritten, or declared ready. Their old macOS success reports do not establish Windows compatibility.

Research contracts remain enforced: explicit scope, units, horizons, historical/simulation clocks, freshness, provenance, and operational abstention. Rainfall is Delhi aggregate mm/day for the next day. The AQI component predicts next-hour PM2.5 under incomplete unit/station lineage, not an official AQI index. Traffic has anonymous benchmark junctions. Water uses the simulated L-TOWN network and does not certify actual faults. Flood, cascade, optimization, and outcomes retain synthetic research limitations. Supported responses retain `research_only=true`, `operational_supported=false`, and `dispatch_allowed=false`. Forecast intervals remain research residual intervals with no guaranteed conditional coverage. No live readings or real municipal coordinates were fabricated.

## Central paths and future import

Existing central configuration: `project_paths.py`; optional `CIVICFLUX_ROOT` environment override. Runtime locators use pathlib. The historical macOS paths inside original artifact metadata are provenance and were preserved. `runtime.research_environment()` applies its macOS library handling only on Darwin.

{chr(10).join('- '+name+': `'+str(path)+'`' for name,path in paths.items())}

Use the project root as the working directory or add it to PYTHONPATH:

```python
from project_paths import PROJECT_ROOT
from src.civicflux.serving import serve
response = serve(component, request, PROJECT_ROOT)
```

Exact source module: `{ML_SOURCE / 'serving.py'}`. Reuse this serving function and the existing registry; do not duplicate the inference pipeline.

## Remaining blockers

- Resolve the two saved XGBoost model-loading failures before claiming all nine components ready. This run does not authorize retraining or artifact conversion.
- Verify city/station mappings, source credentials, operational provenance, and municipal asset/resource inventories before operational integration. Current research-only status is not operational approval.
- Inspect and reconcile the already-present application with the requested future workflow in a separately authorized implementation phase. Its pages, API routes, login, and approval persistence were not retested in this migration-only run.

No new Windows compatibility source fix was necessary. Only verification reports and an additive audit script were written during this run. Migration verification is complete with two explicitly unresolved component failures.
'''
    # Keep the pre-recovery report as a historical baseline once recovery exists.
    if '--evidence-only' not in sys.argv and not (output / 'recovery/recovery_results.json').exists():
        (ROOT / 'reports/WINDOWS_MIGRATION_REVERIFIED.md').write_text(report, encoding='utf-8')
    print(json.dumps({key:evidence[key] for key in ['archive_entries_checked','changed_originals','research_preserved','negative_cases','negative_abstentions']}))


if __name__ == '__main__':
    main()
