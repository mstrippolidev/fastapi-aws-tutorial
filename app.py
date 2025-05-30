"""
    This is the main file of the application. In here is placed all the business logic.
"""
import os
from typing import  List
from passlib.hash import bcrypt
from mangum import Mangum
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import (FastAPI, Depends, HTTPException, UploadFile)
from fastapi.param_functions import File, Form
from pydantic_models.schemas import (UserCreate, UserResponse, PostResponseUser,
                                     PostResponse, PostCreateImage, PostResponsePaginated,
                                     Token)
load_dotenv()  # load environment variables
from database.services import (get_db, get_user_email, # pylint: disable=wrong-import-position
                               generate_jwt_token, is_valid_user,
                               get_user_by_token, get_image_path, save_post,
                               get_post, update_post, oauth2_scheme, verify_token,
                               get_refresh_token, get_user, delete_refresh_token,
                               add_presigned_url_to_post)
from database.models import (User, Posts)  # pylint: disable=wrong-import-position
from database.database import create_tables  # pylint: disable=wrong-import-position

app = FastAPI()

# Create all tables
# baseModel.metadata.create_all(bind=engine)

PAGE_SIZE = 3
# print('antes del routed')
@app.get('/')
async def hello():
    """
        Initial function for testing
    """
    if not os.getenv('TEST_ENVIRONMENT'):
        print('corriendo test')
        create_tables()
    return {"msg": "Hello wordl from actions"}

@app.post('/api/register', status_code = 201, response_model=Token)
async def create_user(user:UserCreate, db: Session = Depends(get_db)) -> dict:
    """
        Api to register users.
    """
    # Check if user exists
    db_user = await get_user_email(user.email, db)

    if db_user:
        raise HTTPException(status_code=422, detail="Email already registered")
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
        token = await generate_jwt_token(user_model, db=db)
        # response
        # user_dict = UserResponse.from_orm(user_model).dict()
        response = {**token}
    except Exception as e:
        db.rollback()
        print('error', str(e))
        raise HTTPException(status_code=422, detail=f"Unexpected error {str(e)}") from e
    db.commit()
    return response

@app.post('/api/login', response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(),
                     db: Session = Depends(get_db)):
    """
        Api to login
    """
    email = form_data.username
    password = form_data.password
    is_valid, user_db = await is_valid_user(email, password, db)
    if not is_valid:
        raise HTTPException(401, user_db)
    token = await generate_jwt_token(user_db, db)
    return token

@app.post('/api/refresh_token')
async def refresh_token(token:str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
        Validate that refresh token is correct and send a generate a new one
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = await verify_token(token, credentials_exception)
    user_id = payload.get('id')
    if user_id is None:
        raise credentials_exception
    refresh_token_db = await get_refresh_token(user_id, db)
    # Validate that has the same token.
    if refresh_token_db is None or refresh_token_db.refresh_token != token:
        raise credentials_exception

    # Refresh the token on the database
    user_db = await get_user(user_id, db)
    new_token = await generate_jwt_token(user_db)
    refresh_token_db.refresh_token = new_token["refresh_token"]
    db.commit()
    db.refresh(refresh_token_db)
    return new_token

@app.get('/api/logout')
async def logout(user_response: UserResponse = Depends(get_user_by_token),
                 db: Session = Depends(get_db)):
    """
        Delete the refresh_token from the user
    """
    delete_refresh_token(user_response.id, db)
    return {"message": "Logout sucessfull"}

@app.get('/api/current_user', response_model=UserResponse)
async def get_current_user(user_response : UserResponse = Depends(get_user_by_token)):
    """
        Get user details
    """
    return user_response


@app.post('/api/posts', response_model=PostResponse, status_code = 201)
async def create_post(post_request: PostCreateImage,
                    user_response: UserResponse = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """
        Create post with image in str or image base 64
    """
    image_str = post_request.image_str
    image_b64 = post_request.image_b64
    image = await get_image_path(image_str, image_b64, None)
    try:
        post_obj = Posts(**post_request.dict(exclude=["image_str", "image_b64"]),
                         user_id = user_response.id, image = image)
        post_obj = await save_post(post_obj, db)
        response = PostResponse.from_orm(post_obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(422, f"Error {str(e)}") from e
    db.commit()
    add_presigned_url_to_post(response)
    return response.dict()

@app.post("/api/posts/image-file")
async def create_post_image_file(title: str = Form(...), content: str = Form(...),
                    user_response: UserResponse = Depends(get_current_user),
                    db: Session = Depends(get_db),
                    image_file: UploadFile = File(...)):
    """
        Save image with formData
    """
    image = await get_image_path(None, None, image_file)
    try:
        post_obj = Posts(title = title, content = content,
                          user_id = user_response.id, image = image)
        post_obj = await save_post(post_obj, db)
        response = PostResponse.from_orm(post_obj)
    except Exception as e:
        db.rollback()
        raise HTTPException(422, f"Error {str(e)}") from e
    db.commit()
    add_presigned_url_to_post(response)
    return response.dict()

@app.get("/api/posts", response_model=List[PostResponse])
async def get_posts_user(user_response : UserResponse = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """
        Get list of post by authenticate user.
    """
    user_id = user_response.id
    posts_db = await get_post(db, user_id)
    response = []
    for post_obj in posts_db:
        post_model = PostResponse.from_orm(post_obj)
        add_presigned_url_to_post(post_model)
        response.append(post_model)
    return response

@app.get("/api/posts/{post_id}", response_model=PostResponseUser)
async def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    """
        Get post details.
    """
    post = await get_post(db, None, post_id = post_id)
    if not post:
        raise HTTPException(404, "post not found")
    post_model = PostResponse.from_orm(post)
    add_presigned_url_to_post(post_model)
    post.image = post_model.image
    return post

@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def edit_post(post_request: PostCreateImage,post_id: int,
                    db: Session = Depends(get_db),
                    user_response : UserResponse = Depends(get_current_user)):
    """
        Edit single post
    """
    # Find if there is a image
    image_str = post_request.image_str
    image_b64 = post_request.image_b64
    image = await get_image_path(image_str, image_b64, None)

    # Update the post
    post = await update_post(db, post_id, post_request.dict(), user_response, image)
    post_model = PostResponse.from_orm(post)
    add_presigned_url_to_post(post_model)
    return post_model

@app.put("/api/posts/{post_id}/image-file", response_model=PostResponse)
async def edit_post_image_file(post_id: int, title: str = Form(...), # pylint: disable=too-many-arguments
                               content: str = Form(...),
                    db: Session = Depends(get_db),
                    user_response : UserResponse = Depends(get_current_user),
                    image_file: UploadFile = File(...)):
    """
        Edit single post with image in formData
    """
    # Find if there is a image
    image = await get_image_path(None, None, image_file)
    # Update the post
    post = await update_post(db, post_id,
                             {'title': title, 'content': content},
                             user_response, image)
    post_model = PostResponse.from_orm(post)
    add_presigned_url_to_post(post_model)
    return post_model

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db),
                      user_response: UserResponse =
                      Depends(get_current_user)):
    """
        Delete single post
    """
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
    """
        Get all post available with pagination
    """
    try:
        if page < 1:
            raise HTTPException(status_code=400,
                            detail="Page number must be greater than or equal to 1")
        skip = (page - 1) * PAGE_SIZE
        query = db.query(Posts).order_by(Posts.id.desc())
        # Add lookup for search
        if search and len(search) > 0:
            query = query.filter(Posts.title.ilike(f"%{search}%"))
        total_posts = query.count()
        total_pages = (total_posts - 1) // PAGE_SIZE + 1
        if page > 1 and page > total_pages:
            raise HTTPException(422, "Number of page exceded")
        posts = query.offset(skip).limit(PAGE_SIZE).all()
        data = []
        for post_obj in posts:
            post_model = PostResponse.from_orm(post_obj)
            add_presigned_url_to_post(post_model)
            data.append(post_model)
        return {"total": total_posts, "total_pages": total_pages,
                "data": data, "page": page}
    except Exception as e:
        print("Error", str(e))
        raise HTTPException(422, f"Error: {str(e)}") from e
handler = Mangum(app)
print('cargo')
