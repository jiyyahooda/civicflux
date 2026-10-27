"""Regression checks for native recovery, integrity, concurrency and contracts."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import shutil

import numpy as np
import pandas as pd
import pytest
import xgboost

from src.civicflux.integration import fixture
from src.civicflux.portable import load_bundle, reconstruct_bundle
from src.civicflux.serving import discover, serve
from src.civicflux.validation import registry_with_checks

ROOT = Path(__file__).resolve().parents[1]


def entry(component):
    return next(row for row in discover(ROOT) if row['component'] == component)


@pytest.mark.parametrize('component,status', [('traffic','supported_research'), ('flood','supported_simulation')])
def test_recovered_serving_retains_scope_and_approval_contract(component, status):
    request = fixture(component, ROOT)
    response = serve(component, request, ROOT)
    assert response['status'] == status
    assert response['research_only'] and not response['operational_supported']
    assert not response['dispatch_allowed'] and not response['allocation_eligible']
    if component == 'traffic':
        assert response['uncertainty']['level'] == .9
    else:
        assert response['prediction'][0]['synthetic'] is True
    refused = serve(component, {**request, 'purpose':'operational'}, ROOT)
    assert refused['status'] == 'abstained' and refused['prediction'] is None


@pytest.mark.parametrize('component', ['traffic','flood'])
def test_json_and_ubjson_exports_retain_same_model_and_bundle_outputs(component):
    path = ROOT / entry(component)['artifact']
    ubj, _ = reconstruct_bundle(path, path.parent / 'portable-windows/booster.ubj')
    portable_json, _ = reconstruct_bundle(path, path.parent / 'portable-windows/booster.json')
    request = fixture(component, ROOT)
    payload = pd.DataFrame(request['history'] if component == 'traffic' else request['scenarios'])
    pd.testing.assert_frame_equal(ubj.predict(payload), portable_json.predict(payload))


def test_corrupted_portable_export_is_refused(tmp_path):
    selected = entry('traffic')
    original = ROOT / selected['artifact']
    copy = tmp_path / selected['artifact']
    copy.parent.mkdir(parents=True)
    shutil.copy2(original, copy)
    shutil.copytree(original.parent / 'portable-windows', copy.parent / 'portable-windows')
    model = copy.parent / 'portable-windows/booster.ubj'
    model.write_bytes(model.read_bytes() + b'corrupted')
    with pytest.raises(ValueError, match='hash mismatch'):
        load_bundle(tmp_path, selected)


def test_concurrent_bundle_loading_does_not_patch_xgboost():
    method = xgboost.Booster.__setstate__
    selected = entry('flood')
    scenarios = pd.DataFrame(fixture('flood', ROOT)['scenarios'])
    def predict(_):
        return load_bundle(ROOT, selected).predict(scenarios).simulated_flood_probability.to_numpy()
    with ThreadPoolExecutor(max_workers=4) as pool:
        values = list(pool.map(predict, range(8)))
    for result in values[1:]:
        np.testing.assert_array_equal(result, values[0])
    assert xgboost.Booster.__setstate__ is method


def test_readiness_requires_current_portable_export_hashes(tmp_path):
    report = json.loads((ROOT / 'reports/windows/inference/traffic.json').read_text())
    assert report['passed'] and report['runtime_artifact_hashes']
    report['runtime_artifact_hashes'] = {}
    (tmp_path / 'traffic.json').write_text(json.dumps(report))
    traffic = next(row for row in registry_with_checks(ROOT, tmp_path) if row['component'] == 'traffic')
    assert traffic['readiness'] == 'Not ready'
