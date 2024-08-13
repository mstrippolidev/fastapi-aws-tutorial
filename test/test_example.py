from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_default():
    assert 1 == 1

def test_endpoint():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello wordl"}