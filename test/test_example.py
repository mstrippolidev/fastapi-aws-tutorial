import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app import (app)
from database.database import baseModel
from database.services import (get_db, get_user_by_token)
from datetime import datetime
from database.models import (Posts, User, RefreshToken)
from pydantic_models.schemas import UserResponse
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL_TEST = f"postgresql://postgres:{DB_PASSWORD}@localhost:5433/fast_api_db"
print(DB_URL_TEST)
engine = create_engine(DB_URL_TEST)

baseModel.metadata.create_all(bind=engine)
# Test session
TestingSession = sessionmaker(autocommit = False, autoflush = False, bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

USER_MOCK =  {'email': 'something@faj.com', 'name': 'miquel', 'last_name': 'any',
            'created_at': str(datetime.now())}
def override_get_current_user():

    return UserResponse(**USER_MOCK)

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_user_by_token] = override_get_current_user
# app.dependency_overrides[get_current_user] = 

client = TestClient(app)

@pytest.fixture
def db_session():
    baseModel.metadata.create_all(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    baseModel.metadata.drop_all(bind=engine)

@pytest.fixture
def initial_state(db_session):
    user = User(**USER_MOCK)
    post = Posts(
        id = 1,
        title = 'example title',
        content = 'some content',
        user_id = 1,
        image = 'Some image',
        created_at = str(datetime.now())
    )
    db = db_session
    db.add(user)
    db.add(post)
    db.commit()
    user_response = UserResponse.from_orm(user).dict()
    USER_MOCK['id'] = user_response['id']
    with engine.connect() as connection:
        connection.execute(text("SELECT setval('posts_id_seq', (SELECT MAX(id) FROM posts) + 1);"))
        connection.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users) + 1);"))
    
    yield post
    # Delete everything
    db.query(RefreshToken).delete()
    db.query(Posts).delete()
    db.query(User).delete()

def test_default():
    assert 1 == 1

def test_endpoint():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello wordl from actions"}


def test_get_current_user():
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


def test_create_user(initial_state):
    data = {'name': 'something', 'last_name': 'something',
            'password': 'test124.23', 'email': 'invalid email'}
    
    resp = client.post('/api/register', json=data)
    assert resp.status_code == 422
    data['email'] = 'valid@email.com'
    resp = client.post('/api/register', json=data)
    assert resp.status_code == 201
    
