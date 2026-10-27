from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.frontend import FrontendFiles


def test_missing_build_explains_setup_and_build_created_after_start_is_served(tmp_path):
    app = FastAPI()
    build = tmp_path / 'dist'
    app.mount('/', FrontendFiles(build))
    with TestClient(app) as client:
        response = client.get('/')
        assert response.status_code == 503
        assert response.headers['content-type'].startswith('text/html')
        assert 'START-CIVICFLUX.cmd' in response.text
        assert client.get('/api/missing').status_code == 404
        assert client.get('/assets/missing.js').status_code == 404
        build.mkdir()
        (build / 'index.html').write_text('<html><div id="root">CivicFlux</div></html>')
        assert client.get('/').status_code == 200
        assert 'CivicFlux' in client.get('/overview').text
        assert client.get('/assets/missing.js').status_code == 404
        assert client.get('/api/missing').status_code == 404
        assert client.get('/missing.png').status_code == 404
