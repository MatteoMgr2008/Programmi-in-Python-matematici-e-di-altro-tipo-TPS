import os
import tempfile
from fastapi.testclient import TestClient

_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
_tmp.close()
os.environ["MINIPAY_DB_BACKEND"] = "sqlite"
os.environ["MINIPAY_DB"] = _tmp.name
os.environ["BANKING_URL"] = "http://127.0.0.1:8001"

from app import app  # noqa: E402

client = TestClient(app)


def register(name, email):
    return client.post("/api/register", json={
        "name": name, "email": email, "password": "password-demo-123"
    })


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_wallet():
    response = register("Test Uno", "uno@example.com")
    assert response.status_code == 201
    token = response.json()["token"]
    wallet = client.get("/api/wallet", headers={"Authorization": f"Bearer {token}"})
    assert wallet.status_code == 200
    assert wallet.json()["balance"] == 100.0


def test_duplicate_email():
    email = "duplicate@example.com"
    assert register("Test Due", email).status_code == 201
    assert register("Test Due", email).status_code == 409


def test_login_rejects_wrong_password():
    register("Test Tre", "tre@example.com")
    response = client.post("/api/login", json={
        "email": "tre@example.com", "password": "password-sbagliata"
    })
    assert response.status_code == 401
