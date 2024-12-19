
# Tutorial to Deploy FastAPI App in AWS

Welcome to this step-by-step guide on deploying a FastAPI application to AWS using Lambda, S3, and RDS. This repository serves as my personal reference to remember how to set up a FastAPI app in AWS. I've aimed to make the instructions as clear as possible so that anyone else can benefit from it as well.


## Table of Contents
- [About the App](#about-the-app)
    - [Getting Started](#getting-started)
    - [Set Up the Virtual Environment](#set-up-the-virtual-environment)
    - [SQLAlchemy Models](#sqlalchemy-models) 
    - [Overview of Endpoints](#overview-of-endpoints)
    - [JWT Authentication](#jwt-authentication)
- [Setting Up AWS S3](#setting-up-aws-s3) 
    - [Configuring bucket](#configuring-bucket) 
- [Setting Up AWS RDS](#setting-up-aws-rds) 
    - [Configuring RDS for Production](#configuring-rds-for-production) 
- [Deploying with AWS Lambda](#deploying-with-aws-lambda) 
    - [Setting Up Lambda in AWS](#setting-up-lambda-in-aws) 
- [Automating Deployment with GitHub Actions](#automating-deployment-with-github-actions) 
    - [Setting Up the Deployment Pipeline](#setting-up-the-deployment-pipeline) 
- [What's Next](#whats-next) 
    - [Expanding Your Knowledge](#expanding-your-knowledge) 
- [Contribution Guidelines](#contribution-guidelines) 
- [License](#license)
## About the App
FastAPI application is a simple yet powerful platform that allows users to create and manage posts, with the ability to upload images to AWS S3. I'll cover everything from initial setup to integrating advanced AWS services.


### Getting Started 
#### Prerequisites 
- **Python 3.8+** 
- **AWS Account** 
- **Git Installed** 
- **Virtual Environment Setup**

**Clone the Repository**
```bash 
  git clone https://github.com/mstrippolidev/fastapi-aws-tutorial.git
  cd fastapi-aws-tutorial 
```
**Set Up the Virtual Environment**
Create and activate a virtual environment to manage your Python packages:
```bash 
python3 -m venv venv
source venv/bin/activate  # On Windows use 'venv\Scripts\activate'
```

**Install dependecies**
Install the required Python packages using the requirements.txt file:
```bash 
  pip install -r requirements.txt
```

### SSet Up the Virtual Environment
You'll need to configure some environment variables by creating a .env file in the root directory. These variables will store sensitive information and configuration settings:
```Doten
SECRET_JWT=your-secret-for-jwt
BUCKET_NAME=your-bucket-s3-name
AWS_ACCESS_KEY_FASTAPI=your-access-key-for-aws
AWS_SECRET_ACCESS_KEY_FASTAPI=your-secret-key-for-aws
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-db-host

DB_NAME_TEST=your-db-test-name
DB_USER_TEST=your-db-test-user
DB_PASSWORD_TEST=your-db-test-password
DB_HOST_TEST=your-db-test-host
DB_PORT_TEST=your-db-test-port
```
- SECRET_JWT: A secret string used for JWT encoding and decoding.

- BUCKET_NAME: The name of your AWS S3 bucket where images will be stored.

- AWS_ACCESS_KEY_FASTAPI and AWS_SECRET_ACCESS_KEY_FASTAPI: Your AWS credentials with permissions for S3 operations.

- DB_NAME, DB_USER, DB_PASSWORD, DB_HOST: Your database configuration for the main application.

For the testing environment:
DB_NAME_TEST, DB_USER_TEST, DB_PASSWORD_TEST, DB_HOST_TEST, DB_PORT_TEST: Test database configurations. You can set these to any accessible database, but ensure it's reachable by the pipeline to run tests effectively.

### SQLAlchemy Models
I use SQLAlchemy for interacting with our database. Below is an example of User and Post model:
```python
from datetime import datetime, timezone
from passlib.hash import bcrypt
from sqlalchemy.orm import relationship
from sqlalchemy import (Column, Integer, String, ForeignKey)
from database.database import baseModel # pylint: disable=import-error, no-name-in-module


class User(baseModel): # pylint: disable=too-few-public-methods
    """
        Class for user table
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    last_name = Column(String, nullable=True)
    password_hash = Column(String)
    created_at = Column(String, default=datetime.utcnow())
    posts = relationship('Posts', back_populates='user')

    def check_password(self, password:str) -> bool:
        """
            Method to check if password match the hash.
        """
        return bcrypt.verify(password, self.password_hash)

class Posts(baseModel): # pylint: disable=too-few-public-methods
    """
        Model for post table.
    """
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    image = Column(String, nullable=True)
    created_at = Column(String, default=datetime.utcnow())
    # relationship
    user = relationship("User", back_populates='posts')
```
Here User have a relationship one to many with Post model. I add the relationship function to backpolulate post model with their respective user to improve performance.

### Overview of Endpoints
The application provides a variety of endpoints for user authentication and post management. You can explore all the endpoints and test them directly using FastAPI's interactive API docs.

**Accessing API Documentation**
Navigate to http://localhost:8000/docs while the app is running to access the interactive Swagger UI provided by FastAPI. This interface lets you view all available endpoints, their required parameters, and even allows you to make requests directly from your browser.

**User Authentication**
Authentication is managed via JWT tokens. The following endpoints are available for user management:

Register a New User: POST /api/register/

Login: POST /api/login/

Refresh JWT Token: POST /api/refresh_token/

Most endpoints require authentication. You'll need to include the JWT token in the Authorization header as a Bearer token.

**Post Management**
Users can create posts with images, which are stored in an AWS S3 bucket. There are two endpoints for creating posts:
1. Create a Post with JSON Data: POST /api/posts/

Payload: JSON object with the following fields:

title (string): Title of the post.

content (string): Content of the post.

image_str (string, optional): Path to the image file.

image_b64 (string, optional): Base64-encoded image data.

Example:
```Json
{
  "title": "My First Post",
  "content": "This is the content of my first post.",
  "image_b64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/..."
}
```
2. Create a Post with Form Data: POST /api/posts/image-file

Payload: multipart/form-data with the following fields:

title (string): Title of the post.

content (string): Content of the post.

image_file (file, required): Image file to upload.

### JWT Authentication
I use the PyJWT library for handling JWT authentication. To maintain user sessions and refresh tokens when they expire, also I implemented a RefreshToken model and associated logic.

Here's the RefreshToken model:
```python 
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class RefreshToken(Base):
    """
    Model for refresh token table
    """
    __tablename__ = 'refresh_token'
    id = Column(Integer, primary_key=True, index=True)
    refresh_token = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    created_at = Column(String, default=datetime.now(timezone.utc))

```
## Setting Up AWS S3
For upload and store image I use S3 from AWS, here are the steps I do to setting up the bucket in AWS, and in the application layer to handle the images.


#### Creating the S3 Bucket
Log in to your AWS account and go to S3 in the search panel, one you are in the panel for S3:
- Click on Create bucket.
- After tab you will see a tab to configure the bucket, enter a unique Bucket name, you can only use lowercase english letter, numbers, hyphens and dots.
- Choose the AWS Region closest to your application servers.
- Now, you can keep enabled the option 'Block all public access' (Recommended) or disabled, but if you disabled keep in mind that whatever person can access the bucket, so you cannot save sensitive data there and you are expose to malicious attack.
- Click in create bucket.

#### Configuring Bucket Permissions
Now you can begin upload files to the bucket but you cannot see the files if you try to access through the browser. For that we need to add permissions to the bucket.
There are several ways to do it, so, I'll explain from the less recommended to the more recommended.

Option 1: Public Bucket: Making the bucket public allows anyone to access the images via a URL. This is not recommended due to security risks.
Steps:
- Go to the Permissions tab of your bucket.
- Click Edit under Block public access settings.
- Unchecked Block all public access, if you have checked it, and confirm
- Below in bucket policy add this
```Json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```
Change the parameter your-bucket-name for your actual bucket name, and click save changes.
Now you can access your image through the browser.

Option 2: Private Bucket with Pre-signed URLs
This is a better approach an actually what I use that is generate pre-signed URLs for accessing images. This method enhances security by granting temporary access to specific objects without exposing the entire bucket.
- Ensure that Block all public access is enabled in your bucket settings. You can see if it's enabled in the permissions tab.
- Use AWS SDKs (like boto3 in Python) to generate pre-signed URLs when users request access to an image.
```python 
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

```
This function generate a presigned url for the bucket and set an expiretion time to one hour.

Option 3: Using CloudFront for Secure Distribution
The best method is to use CloudFront (Amazon Content Delivery Network) not only improve the performance of the app but also help you to hide the bucket_name, improving the security.
