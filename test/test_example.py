"""
    File to test api endpoint for creating users
"""
from .utils import *
from database.services import (get_db, get_user_by_token)

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_user_by_token] = override_get_current_user


def test_default():
    assert 1 == 1

def test_endpoint():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello wordl from actions"}


def test_get_current_user(initial_state):
    response = client.get('/api/current_user')
    assert response.status_code == 200
    json = response.json()
    fields = ['email', 'name', 'last_name']
    for field in fields:
        assert field in json
        assert field in USER_MOCK
        assert json[field] == USER_MOCK[field]

def test_get_posts(initial_state):
    response = client.get('/api/posts')
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_create_user(db_session):
    data = {'name': 'something', 'last_name': 'something',
            'password': 'test124.23', 'email': 'invalid email'}
    resp = client.post('/api/register', json=data)
    assert resp.status_code == 422
    data['email'] = 'valid@email.com'
    resp = client.post('/api/register', json=data)
    assert resp.status_code == 201
