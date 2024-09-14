"""
    test for posts
"""
from database.services import (get_db, get_user_by_token)
from test.utils import *
from database.models import Posts
from app import app

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_user_by_token] = override_get_current_user

def test_post_create(initial_state):
    """
        Test for create a post
    """
    data = {'title': 'example title', 'content': 'some content',
            'image_str': 'some_path_image'}
    resp = client.post('/api/posts', json=data)
    assert resp.status_code == 201
    json = resp.json()
    assert json['title'] == data['title']
    assert json['content'] == data['content']

def test_get_post_details(initial_state):
    """
        Test post details
    """
    post_id = initial_state.id
    resp = client.get(f'/api/posts/{post_id}')
    assert resp.status_code == 200
    data = resp.json()
    assert initial_state.title == data['title']
    assert initial_state.content == data['content']

def test_get_post_details_not_found(initial_state):
    post_id = 999
    resp = client.get(f'/api/posts/{post_id}')
    assert resp.status_code == 404
    

def test_edit_post(initial_state):
    data_edit = {'title': 'title edit', 'content': 'content edit'}
    post_id = initial_state.id
    resp = client.put(f'/api/posts/{post_id}', json=data_edit)
    assert resp.status_code == 200
    data = resp.json()
    assert initial_state.title != data['title']
    assert initial_state.content != data['content']
    assert data_edit['title'] == data['title']
    assert data_edit['content'] == data['content']
    
def test_edit_post_fail(initial_state):
    data_edit = {'title': 'title edit', 'content': 'content edit'}
    post_id = 999
    resp = client.put(f'/api/posts/{post_id}', json=data_edit)
    assert resp.status_code == 404

def test_delete_post(initial_state):
    post_id = initial_state.id
    resp = client.delete(f'/api/posts/{post_id}')
    assert resp.status_code == 200
    db = TestingSession()
    post = db.query(Posts).filter(Posts.id == post_id).first()
    assert post is None

def test_delete_post(initial_state):
    post_id = 1111
    resp = client.delete(f'/api/posts/{post_id}')
    assert resp.status_code == 404