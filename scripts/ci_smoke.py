"""Native-platform smoke checks using committed artifacts, without downloading data."""
from pathlib import Path
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['CIVICFLUX_PUBLIC_FEEDS'] = '0'
# All writes go to disposable local state. No real credentials or datasets are used.
with tempfile.TemporaryDirectory(prefix='civicflux-ci-') as temp:
    os.environ['CIVICFLUX_DB'] = str(Path(temp) / 'test.sqlite3')
    os.environ['CIVICFLUX_ADMIN_PASSWORD'] = 'temporary-ci-fixture'
    from src.civicflux.serving import discover, serve
    from src.civicflux.portable import load_bundle
    from src.civicflux.integration import fixture, negative_requests
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend import config

    entries = discover(ROOT)
    assert len(entries) == 9
    for entry in entries:
        if entry.get('artifact'):
            assert load_bundle(ROOT, entry) is not None
        print('Loaded:', entry['component'])
    for component in ('flood', 'cascade_risk', 'resource_optimization', 'intervention_outcomes'):
        request = fixture(component, ROOT)
        result = serve(component, request, ROOT)
        assert result['status'] in ('supported_research', 'supported_simulation'), result
        for case in negative_requests(component, request).values():
            assert serve(component, case, ROOT)['status'] == 'abstained'
        print('Prediction and abstention passed:', component)
    with TestClient(app) as client:
        for path in ('/api/health', '/docs', '/openapi.json', '/api/models', '/api/cities'):
            assert client.get(path).status_code == 200, path
        models = client.get('/api/models').json()
        assert all(row['readiness'] != 'Not ready' for row in models), models
        assert client.post('/api/auth/login', json={'username': config.ADMIN_ID, 'password': '110001'}).status_code == 200
        scenario = client.get('/api/scenarios/defaults').json()
        response = client.post('/api/scenarios', json=scenario)
        assert response.status_code in (200, 201), response.text
        assert client.get('/api/scenarios').json()
        assert client.get('/api/feedback').status_code == 200
        assert client.post('/api/auth/logout').status_code == 200
    print('Model loading, API, SQLite, flood/cascade and planning smoke checks passed.')
