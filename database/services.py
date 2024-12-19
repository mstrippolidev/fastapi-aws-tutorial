"""
    This file contains the business logic for the user and post
"""
import os
import base64
import random
import string
import re
from datetime import (datetime, timedelta, timezone)
import mimetypes
import boto3
import jwt
from fastapi import  (Depends, HTTPException, UploadFile, Security)
from fastapi.security import (OAuth2PasswordBearer)
from sqlalchemy.orm import (Session, joinedload)
from database.database import (baseModel, # pylint: disable=import-error, no-name-in-module
                               engine, SessionLocal)
from database.models import (User, Posts, RefreshToken) # pylint: disable=import-error, no-name-in-module

from pydantic_models.schemas import (UserResponse, PostResponse)

SECRET_JWT = os.getenv("SECRET_JWT")

MEDIA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "media")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_FASTAPI")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY_FASTAPI")
s3 = boto3.client('s3', aws_access_key_id = aws_access_key_id,
                  aws_secret_access_key=aws_secret_access_key)
BUCKET_NAME = os.getenv("BUCKET_NAME")
REFRESH_TOKEN_EXPIRE_DAYS = 7

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

async def get_user(user_id: int, db: Session) -> User:
    """
        Get the user id from the db
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(404,detail="User not found")
    return user

async def get_user_email(email:str, db: Session) -> User:
    """
        Method to get a user by email
    """
    db_user = db.query(User).filter(User.email.ilike(email)).first()
    return db_user

async def verify_token(token: str, credentials_exception):
    """
        Verify if is a valid token and is not expired
    """
    try:
        payload = jwt.decode(token, SECRET_JWT, algorithms=["HS256"])
    except Exception as exe:
        raise credentials_exception from exe
    # Token is not expired
    exp = payload.get('exp')
    if exp is None or datetime.utcfromtimestamp(exp) < datetime.utcnow():
        raise credentials_exception
    return payload


async def encode_token(user: User, minutes: int = 60):
    """
        Function to encode a token
    """
     # Convert user model to user schema with the from_orm method of pedantyc
    schema_user = UserResponse.from_orm(user)
    # Convert to dict
    user_dict = schema_user.dict(exclude='created_at')
    jwt_dict = {**user_dict,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes)}
    # Create the JWT
    token = jwt.encode(jwt_dict, SECRET_JWT, algorithm="HS256")

    return token


async def save_refresh_token(user_id: int, refresh_token: str, db : Session):
    """
        Save the refresh token to the database
    """
    print('saving the refresh token')
    refresh_token_db = RefreshToken(user_id = user_id, refresh_token = refresh_token)
    db.add(refresh_token_db)
    db.commit()


async def get_refresh_token(user_id: int, db: Session):
    """
        Function to get the refresh_token from a user
    """
    refresh_token = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).first()
    return refresh_token

async def get_or_create_refresh_token(user: User, db: Session):
    """
        Function to get or create refresh token
    """
    refresh_token_db = None
    # Only one user per token, get the current user token if exists
    # Feach the refresh token for this user
    refresh_token_db = await get_refresh_token(user.id, db)
    if refresh_token_db is None:
        refresh_token = await encode_token(user, REFRESH_TOKEN_EXPIRE_DAYS * 60 * 24)
        await save_refresh_token(user.id, refresh_token, db)
    else:
        refresh_token = refresh_token_db.refresh_token
    return refresh_token

async def generate_jwt_token(user: User, db: Session = None) -> dict:
    """
        Method to generate a jwt token
    """
    # Create token for this user
    token = await encode_token(user)
    refresh_token = await get_or_create_refresh_token(user, db)
    return {"access_token": token, "token_type": "Bearer",
            "refresh_token": refresh_token}

async def delete_refresh_token(user_id: int, db: Session):
    """
        Delete the refresh token from the user
    """
    db_token = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).first()
    if db_token:
        db.delete(db_token)
        db.commit()

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

async def get_user_by_token(token: str = Security(oauth2_scheme),db: Session = Depends(get_db),
                            ) -> UserResponse:
    """
        Verify if the token is on the headers of the request
    """
    try:
        # Decode the token and get the user_id from it
        payload = jwt.decode(token, SECRET_JWT, algorithms=["HS256"])
    except Exception as e:
        raise HTTPException(422, f"Error {str(e)}") from e

    user_db = db.query(User).get(payload['id'])
    if not user_db:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Check if the token has expired
    exp = payload.get("exp")
    if exp is None or datetime.utcfromtimestamp(exp) < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token has expired")
    user_schema = UserResponse.from_orm(user_db)
    return user_schema

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
            s3.put_object(Bucket = BUCKET_NAME,
                          Key=image_name,
                          Body=image_data,
                          ContentType=my_format.replace('data:', '')
                          )
            image_url_path = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_name}"
            return image_url_path
        except Exception as e:
            raise HTTPException(status_code=400,
                                detail=f"Invalid base64 image data {str(e)}" ) from e
    if image_file:
        try:
            content_type, _ = mimetypes.guess_type(image_file.filename)
            if content_type is None:
                content_type = 'application/octet-stream'
            # Upload the image file to S3
            s3.upload_fileobj(image_file.file, BUCKET_NAME, image_file.filename,
                        ExtraArgs={'ContentType': content_type})
            image_url_path = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_file.filename}"
            return image_url_path
        except Exception as e:
            raise HTTPException(400, f"Invalid image file {str(e)}") from e
    return None

def generate_signed_url(object_key:str,exp:int = 3600):
    """
        Generate a signed url for the bucket
    """
    url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': object_key},
        ExpiresIn=exp)
    return url

def add_presigned_url_to_post(post:PostResponse):
    """
        Change the image field for the presigned url
    """
    if post.image is not None and post.image.startswith(f'https://{BUCKET_NAME}.s3.amazonaws.com'):
        object_key = post.image.split('/')
        object_key = object_key[-1]
        signed_url = generate_signed_url(object_key)
        post.image = signed_url

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
