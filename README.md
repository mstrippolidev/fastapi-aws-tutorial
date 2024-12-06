
# Tutorial to Deploy FastAPI App in AWS

Welcome to this step-by-step guide on deploying a FastAPI application to AWS using Lambda, S3, and RDS. This repository serves as my personal reference to remember how to set up a FastAPI app in AWS. I've aimed to make the instructions as clear as possible so that anyone else can benefit from it as well.


## Table of Contents
- [About the App](#about-the-app)
    - [Getting Started](#getting-started)
    - [User Posts](#user-posts)
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
