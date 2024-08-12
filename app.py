from fastapi import FastAPI, Depends, HTTPException, UploadFile
from dotenv import load_dotenv

load_dotenv()  # load environment variables

from fastapi.security import OAuth2PasswordRequestForm
from pydantic_models.schemas import (UserCreate, UserResponse, PostResponseUser, 
                                     PostResponse, PostCreateImage, PostResponsePaginated)
from database.services import (get_db, get_user_email, 
                               generate_jwt_token, is_valid_user,
                               get_user_by_token, get_image_path, save_post, 
                               get_post, update_post, serializer_post)
from sqlalchemy.orm import Session
from database.models import User, Posts
from passlib.hash import bcrypt
from typing import  List
from mangum import Mangum
from fastapi.param_functions import File, Form
from datetime import datetime
from fastapi.responses import JSONResponse
import json

app = FastAPI()

# Create all tables
# baseModel.metadata.create_all(bind=engine)

PAGE_SIZE = 3
print('antes del routed')
@app.get('/')
async def hello():
    return {"msg": "Hello wordl"}

@app.post('/api/register')
async def create_user(user:UserCreate, db: Session = Depends(get_db)) -> dict:
    print('iniciando')
    # Check if user exists
    db_user = await get_user_email(user.email, db)

    if db_user:
        raise HTTPException(status_code=422, detail="Email already registered")
    print('obteniendo usuario')
    # Create the user
    password_hash = bcrypt.hash(user.password)
    user_model = User(name=user.name, email=user.email, last_name = user.last_name,
                      password_hash = password_hash)
    try:
        # Add user to the db
        db.add(user_model)
        db.flush()
        db.refresh(user_model)

        # Generate token and response
        token = await generate_jwt_token(user_model)

        # response
        # user_dict = UserResponse.from_orm(user_model).dict()
        response = {**token}
    
        
    except Exception as e:
        db.rollback()
        print('error', str(e))
        raise HTTPException(status_code=422, detail="Unexpected error %s" % str(e))
    
    else:
        db.commit()
        print("ok", response)
        return response
    
@app.post('/api/login')
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username
    password = form_data.password

    isValid, user_db = await is_valid_user(email, password, db)

    if not isValid:
        raise HTTPException(401, user_db)
    
    token = await generate_jwt_token(user_db)

    return token

@app.get('/api/current_user', response_model=UserResponse)
async def get_current_user(user_response : UserResponse = Depends(get_user_by_token)):
    return user_response


@app.post('/api/posts', response_model=PostResponse)
async def create_post(post_request: PostCreateImage,
                    user_response: UserResponse = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    
    image_str = post_request.image_str
    image_b64 = post_request.image_b64
    image = await get_image_path(image_str, image_b64, None)
    try:
        post_obj = Posts(**post_request.dict(exclude=["image_str", "image_b64"]), user_id = user_response.id, image = image)
        post_obj = await save_post(post_obj, db)
        response = PostResponse.from_orm(post_obj).dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(422, "Error %s" % str(e))
    
    else:
        db.commit()
        return response
    
@app.post("/api/posts/image-file")
async def create_post_image_file(title: str = Form(...), content: str = Form(...),
                    user_response: UserResponse = Depends(get_current_user),
                    db: Session = Depends(get_db), 
                    image_file: UploadFile = File(...)):
    print('iniciando image')
    image = await get_image_path(None, None, image_file)
    try:
        print('this is the image path', image)
        post_obj = Posts(title = title, content = content,
                          user_id = user_response.id, image = image)
        post_obj = await save_post(post_obj, db)
        response = PostResponse.from_orm(post_obj).dict()
        
    except Exception as e:
        print('error', str(e))
        db.rollback()
        raise HTTPException(422, "Error %s" % str(e))
    
    else:
        db.commit()
        return response
    


@app.get("/api/posts", response_model=List[PostResponse])
async def get_posts_user(user_response : UserResponse = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    
    user_id = user_response.id
    posts_db = await get_post(db, user_id)
    return posts_db


@app.get("/api/posts/{post_id}", response_model=PostResponseUser)
async def get_post_detail(post_id: int, db: Session = Depends(get_db)):

    post = await get_post(db, None, id = post_id)
    if not post:
        raise HTTPException(404, "post not found")
    return post


@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def edit_post(post_request: PostCreateImage,post_id: int,
                    db: Session = Depends(get_db),
                    user_response : UserResponse = Depends(get_current_user)):

    # Find if there is a image
    image_str = post_request.image_str
    image_b64 = post_request.image_b64
    image = await get_image_path(image_str, image_b64, None)

    # Update the post
    post = await update_post(db, post_id, post_request.dict(), user_response, image)
    
    return post

@app.put("/api/posts/{post_id}/image-file", response_model=PostResponse)
async def edit_post(post_id: int, title: str = Form(...), content: str = Form(...),
                    db: Session = Depends(get_db),
                    user_response : UserResponse = Depends(get_current_user),
                    image_file: UploadFile = File(...)):

    # Find if there is a image
    image = await get_image_path(None, None, image_file)

    # Update the post
    post = await update_post(db, post_id, {'title': title, 'content': content}, user_response, image)
    
    return post


@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db),
                      user_response: UserResponse = Depends(get_current_user)):
    

    post = await get_post(db, None, post_id)

    if not post:
        raise HTTPException(404, "Post not found")
    
    if post.user_id != user_response.id:
        raise HTTPException(403, "Unathorized")

    db.delete(post)
    db.commit()
    return "Post deleted"


@app.get("/api/posts-all", response_model=PostResponsePaginated)
async def get_posts_all(page: int = 1, search: str = None,
                   db: Session = Depends(get_db)):
    try:
        if page < 1:
            raise HTTPException(status_code=400, detail="Page number must be greater than or equal to 1")
        skip = (page - 1) * PAGE_SIZE
        query = db.query(Posts).order_by(Posts.id.desc())
        # Add lookup for search
        if search and len(search) > 0:
            query = query.filter(Posts.title.ilike(f"%{search}%"))
        total_posts = query.count()
        total_pages = (total_posts - 1) // PAGE_SIZE + 1  # Calculate the total number of pages
        
        if page > 1 and page > total_pages:
            raise HTTPException(422, "Number of page exceded")
        
        posts = query.offset(skip).limit(PAGE_SIZE).all()
        # post_list = []
        # # Create list of post
        # for post in posts:
        #     post_list.append(await serializer_post(post))
        # Seriaizer response
        # post_response =  PostResponsePaginated(**{"total": total_posts, ...}) return post_response.dict
        return {"total": total_posts, "total_pages": total_pages, "data": posts, "page": page}
    except Exception as e:
        print("Error", str(e))
        raise HTTPException(422, "Error: %s" % (str(e)))
print('al final')
handler = Mangum(app)