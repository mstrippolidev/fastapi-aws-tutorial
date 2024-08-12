from database.database import baseModel, engine, SessionLocal
from database.models import User, Posts
from sqlalchemy.orm import Session, joinedload
from pydantic_models.schemas import UserResponse, PostResponse
import database.models, jwt, os, base64, random, string, re, boto3
from datetime import datetime, timedelta
from fastapi import  Depends, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer

SECRET_JWT = os.getenv("SECRET_JWT")

MEDIA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "media")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


aws_access_key_id = os.getenv("AWS_ACCESS_KEY_FASTAPI")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY_FASTAPI")
s3 = boto3.client('s3', aws_access_key_id = aws_access_key_id, 
                  aws_secret_access_key=aws_secret_access_key)
BUCKET_NAME = os.getenv("BUCKET_NAME")


def create_db():
    return baseModel.metadata.create_all(bind = engine)



# If you run this file will create the sqlite db 'mydb'
# create_db()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# create_db(); Import the models to create the tables inside the DB sqlite

async def get_user_email(email:str, db: Session) -> User:
    db_user = db.query(User).filter(User.email.ilike(email)).first()
    return db_user

async def generate_jwt_token(user: User) -> dict:
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

    user_db = await get_user_email(email, db)
    if not user_db:
        return (False, "Email user doesn't exists")
    
    if not user_db.check_password(password):
        return (False, "Wrong password!!")
    
    return (True, user_db)


"""The ouath_schema execute the code to verify if the token is in the headers"""
async def get_user_by_token(db: Session = Depends(get_db), 
                            token: str = Depends(oauth2_scheme)) -> UserResponse:

    try:
        # Decode the token and get the user_id from it
        payload = jwt.decode(token, SECRET_JWT, algorithms=["HS256"])
        user_db = db.query(User).get(payload['id'])
        user_schema = UserResponse.from_orm(user_db)
        return user_schema
    except Exception as e:
        raise HTTPException(422, "Error %s" % str(e))
    

async def get_extension_from_base64(base64_str: str):
    mime_type = re.search(r"data:(.*);base64", base64_str).group(1)
    extension = mime_type.split("/")[-1]
    return extension

async def get_image_path(image_str:str, image_b64:str, image_file: UploadFile):
    
    image_name = ""
    for _ in range(11):
        image_name += random.choice(string.ascii_lowercase)

    if image_str:
        return image_str
    
    # Image in the format b64
    if image_b64:
        try:
            format, imgstr =  image_b64.split(';base64,')
            # Acceder al ultimo miembro de la list
            extension = format.split('/')[-1]
            image_name = "%s.%s" % (image_name, extension)
            image_data = base64.b64decode(imgstr)

            image_path = os.path.join(MEDIA_DIR, image_name)
            with open(image_path, "wb") as f:
                f.write(image_data)
            image_url_path = f"/media/{os.path.basename(image_path)}"
            return image_url_path
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid base64 image data %s" % str(e))
        

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
            raise Exception(400, "Invalid image file %s" % str(e))
        
    return None


async def save_post(post: Posts, db: Session):
    db.add(post)
    db.flush()
    db.refresh(post)
    return post


async def get_post(db: Session, user_id: int, id: int = None):
    query = db.query(Posts)
    
    if id is not None:
        return query.options(joinedload(Posts.user)).get(id)
    
    
    posts = query.filter(Posts.user_id == user_id).order_by(Posts.id.desc()).all()
    return posts


async def update_post(db: Session, post_id: int, params: dict,
                     user_response: UserResponse ,image = None):
    
    post = await get_post(db, None, id = post_id)
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

    db.commit()
    db.refresh(post)

    return post


async def serializer_post(post: Posts):
    post_app = PostResponse.from_orm(post)
    return post_app.dict()