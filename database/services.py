"""
    This file contains the business logic for the user and post
"""
import os
import base64
import random
import string
import re
from datetime import (datetime, timedelta)
import boto3
import jwt
from fastapi import  (Depends, HTTPException, UploadFile)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import (Session, joinedload)
from database.database import (baseModel, # pylint: disable=import-error, no-name-in-module
                               engine, SessionLocal)
from database.models import (User, Posts) # pylint: disable=import-error, no-name-in-module

from pydantic_models.schemas import (UserResponse, PostResponse)

SECRET_JWT = os.getenv("SECRET_JWT")

MEDIA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "media")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_FASTAPI")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY_FASTAPI")
s3 = boto3.client('s3', aws_access_key_id = aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key)
BUCKET_NAME = os.getenv("BUCKET_NAME")

def create_db():
    """
        Funcion to return a db and all tables.
    """
    return baseModel.metadata.create_all(bind = engine)

# Dependency to get the database session
def get_db():
    """
        Method to create a local session to the DB
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_user_email(email:str, db: Session) -> User:
    """
        Method to get a user by email
    """
    db_user = db.query(User).filter(User.email.ilike(email)).first()
    return db_user

async def generate_jwt_token(user: User) -> dict:
    """
        Method to generate a jwt token
    """
    # Convert user model to user schema with the from_orm method of pedantyc
    schema_user = UserResponse.from_orm(user)
    # Convert to dict
    user_dict = schema_user.dict(exclude='created_at')
    jwt_dict = {**user_dict,
                "exp": datetime.utcnow() + timedelta(minutes=60)}
    # Create the JWT
    token = jwt.encode(jwt_dict, SECRET_JWT, algorithm="HS256")

    return {"access_token": token, "token_type": "Bearer"}

async def is_valid_user(email:str, password:str, db: Session):
    """
        Verify if a password match the hash from a user
    """
    user_db = await get_user_email(email, db)
    if not user_db:
        return (False, "Email user doesn't exists")
    if not user_db.check_password(password):
        return (False, "Wrong password!!")
    return (True, user_db)

async def get_user_by_token(db: Session = Depends(get_db),
                            token: str = Depends(oauth2_scheme)) -> UserResponse:
    """
        Verify if the token is on the headers of the request
    """
    try:
        # Decode the token and get the user_id from it
        payload = jwt.decode(token, SECRET_JWT, algorithms=["HS256"])
        user_db = db.query(User).get(payload['id'])
        user_schema = UserResponse.from_orm(user_db)
        return user_schema
    except Exception as e:
        raise HTTPException(422, f"Error {str(e)}") from e
async def get_extension_from_base64(base64_str: str):
    """
        Function to get the extension from a base64 string
    """
    mime_type = re.search(r"data:(.*);base64", base64_str).group(1)
    extension = mime_type.split("/")[-1]
    return extension

async def get_image_path(image_str:str, image_b64:str, image_file: UploadFile):
    """
        Get image path depends of the parameters
    """
    image_name = ""
    for _ in range(11):
        image_name += random.choice(string.ascii_lowercase)

    if image_str:
        return image_str
    # Image in the format b64
    if image_b64:
        try:
            my_format, imgstr =  image_b64.split(';base64,')
            # Acceder al ultimo miembro de la list
            extension = my_format.split('/')[-1]
            image_name = f"{image_name}.{extension}"
            image_data = base64.b64decode(imgstr)

            image_path = os.path.join(MEDIA_DIR, image_name)
            with open(image_path, "wb") as f:
                f.write(image_data)
            image_url_path = f"/media/{os.path.basename(image_path)}"
            return image_url_path
        except Exception as e:
            raise HTTPException(status_code=400,
                                detail=f"Invalid base64 image data {str(e)}" ) from e
    if image_file:
        try:
            # image_path = os.path.join(MEDIA_DIR, image_file.filename)
            # with open(image_path, "wb") as f:
            #     f.write(await image_file.read())

            # image_url_path = f"/media/{os.path.basename(image_path)}"
            # Upload the image file to S3
            s3.upload_fileobj(image_file.file, BUCKET_NAME, image_file.filename)
            image_url_path = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_file.filename}"
            return image_url_path
        except Exception as e:
            raise HTTPException(400, f"Invalid image file {str(e)}") from e
    return None

async def save_post(post: Posts, db: Session):
    """
        Save post to the DB
    """
    db.add(post)
    db.flush()
    db.refresh(post)
    return post

async def get_post(db: Session, user_id: int, post_id: int = None):
    """
        Get a single post from the db
    """
    query = db.query(Posts)
    if post_id is not None:
        return query.options(joinedload(Posts.user)).get(post_id)
    posts = query.filter(Posts.user_id == user_id).order_by(Posts.id.desc()).all()
    return posts

async def update_post(db: Session, post_id: int, params: dict,
                     user_response: UserResponse ,image = None):
    """
        Function to update a post.
    """
    post = await get_post(db, None, post_id = post_id)
    if not post:
        raise HTTPException(404, "post not found")
    # Only the user who made the post can edit it
    user_id = user_response.id
    if user_id != post.user_id:
        raise HTTPException(403, "Unathorized")
    for field, value in params.items():
        if hasattr(post, field):
            setattr(post, field, value)
        if image is not None:
            post.image = image
    # Commit to db
    db.commit()
    db.refresh(post)
    return post

async def serializer_post(post: Posts):
    """
        Function to serialize a post
    """
    post_app = PostResponse.from_orm(post)
    return post_app.dict()
