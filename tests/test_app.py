from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"


def test_example_api():
    r = client.get("/api/example")
    assert r.status_code == 200
    data = r.json()
    assert "example" in data.get("message", "")


def test_predict():
    r = client.post("/predict", json={"text": "There was an error connecting to DB"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("label") == "incident"
