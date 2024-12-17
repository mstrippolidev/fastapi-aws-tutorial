
# Tutorial to Deploy FastAPI App in AWS

Welcome to this step-by-step guide on deploying a FastAPI application to AWS using Lambda, S3, and RDS. This repository serves as my personal reference to remember how to set up a FastAPI app in AWS. I've aimed to make the instructions as clear as possible so that anyone else can benefit from it as well.


## Table of Contents
- [About the App](#about-the-app)
    - [Getting Started](#getting-started)
    - [Set Up the Virtual Environment](#set-up-the-virtual-environment)
    - [SQLAlchemy Models](#sqlalchemy-models) 
    - [Overview of Endpoints](#overview-of-endpoints)
    - [JWT Authentication](#jwt-authentication) 
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
Our FastAPI application is a simple yet powerful platform that allows users to create and manage posts, with the ability to upload images to AWS S3. We'll cover everything from initial setup to integrating advanced AWS services.


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
I use SQLAlchemy for interacting with our database. Below is an example of user and Post model:
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
