
# Tutorial to Deploy FastAPI App in AWS

Welcome to this step-by-step guide on deploying a FastAPI application to AWS using Lambda, S3, and RDS. This repository serves as my personal reference to remember how to set up a FastAPI app in AWS. I've aimed to make the instructions as clear as possible so that anyone else can benefit from it as well.


## Table of Contents
- [About the App](#about-the-app)
    - [Getting Started](#getting-started)
    - [SQLAlchemy Models](#sqlalchemy-models) 
    - [Pydantic Models](#pydantic-models) 
    - [JWT Authentication](#jwt-authentication) 
    - [Integrating S3](#integrating-s3)
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
