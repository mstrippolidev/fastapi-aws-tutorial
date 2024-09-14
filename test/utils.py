"""
    File for utils test
"""
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app import app
from database.database import baseModel
from datetime import datetime
from database.models import (Posts, User, RefreshToken)
from pydantic_models.schemas import UserResponse

client = TestClient(app)
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL_TEST = f"postgresql://postgres:{DB_PASSWORD}@localhost:5433/fast_api_db"
print(DB_URL_TEST, 'Este es el url!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
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

USER_MOCK =  {'id': 1, 'email': 'something@faj.com', 'name': 'miquel', 'last_name': 'any',
            'created_at': str(datetime.now())}
def override_get_current_user():

    return UserResponse(**USER_MOCK)


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
    yield post
    # Delete everything
    db.query(RefreshToken).delete()
    db.query(Posts).delete()
    db.query(User).delete()
    with engine.connect() as connection:
        connection.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1;"))
        connection.execute(text("ALTER SEQUENCE posts_id_seq RESTART WITH 1;"))
        # connection.execute(text("SELECT setval('posts_id_seq', (SELECT MAX(id) FROM posts) + 1);"))
        # connection.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users) + 1);"))
