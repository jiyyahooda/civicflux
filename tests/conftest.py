from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend import config
from backend.main import app

@pytest.fixture(autouse=True)
def no_live_network_in_unit_tests(monkeypatch):
    monkeypatch.setenv('CIVICFLUX_PUBLIC_FEEDS','0')
    monkeypatch.delenv('DATA_GOV_IN_API_KEY',raising=False)
    monkeypatch.delenv('CIVICFLUX_IMD_URL',raising=False)
    monkeypatch.delenv('CIVICFLUX_CPCB_URL',raising=False)
    monkeypatch.delenv('SENDER_EMAIL',raising=False)
    monkeypatch.delenv('SENDER_PASSWORD',raising=False)
    monkeypatch.setenv('SMTP_USER','test@example.org')
    monkeypatch.delenv('SMTP_PASS',raising=False)
    from backend.services import complaint_email
    monkeypatch.setattr(complaint_email,'transport',lambda message:None)

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(config,'DB_PATH',tmp_path/'test.sqlite3')
    monkeypatch.setattr(config,'ADMIN_ID','admin')
    monkeypatch.setattr(config,'ADMIN_PASSWORD','110001')
    with TestClient(app) as client: yield client

@pytest.fixture
def admin_client(client):
    response=client.post('/api/auth/login',json={'username':config.ADMIN_ID,'password':config.ADMIN_PASSWORD})
    assert response.status_code==200
    return client


@pytest.fixture(autouse=True)
def isolated_sms_provider(monkeypatch):
    from backend.api import civilian
    from civilian_helpers import SENT
    SENT.clear()
    monkeypatch.setenv('FAST2SMS_MODE','smart')
    monkeypatch.setenv('FAST2SMS_API_KEY','test-only-not-a-real-key')
    monkeypatch.setenv('FAST2SMS_OTP_TEMPLATE_ID','test-only-template')
    async def accept(phone,code):SENT[phone]=code
    monkeypatch.setattr(civilian,'sms_send',accept)

@pytest.fixture
def civilian_account(client):
    from civilian_helpers import sign_in
    return sign_in(client)
