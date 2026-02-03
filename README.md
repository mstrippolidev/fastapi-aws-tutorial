
# Tutorial to Deploy FastAPI App in AWS as Lambda function

Welcome to this step-by-step guide on deploying a FastAPI application to AWS using Lambda, S3, and RDS in a private VPC. We also learn different methods to see our images through S3 and cloudFront, and finally we make a s3 endpoint to upload our image through the private red of AWS. This repository serves as my personal reference to remember how to set up a FastAPI app in AWS. I've aimed to make the instructions as clear as possible so that anyone else can benefit from it as well.

<img width="1200" height="700" alt="Code_Generated_Image (2)" src="https://github.com/user-attachments/assets/15536dbe-9374-436f-8937-759fd0a9b1f7" />


## Table of Contents
- [About the App](#about-the-app)
    - [Getting Started](#getting-started)
    - [Set Up the Virtual Environment](#set-up-the-virtual-environment)
    - [SQLAlchemy Models](#sqlalchemy-models) 
    - [Overview of Endpoints](#overview-of-endpoints)
    - [JWT Authentication](#jwt-authentication)
- [Setting Up AWS S3](#setting-up-aws-s3) 
    - [Creating S3 Bucket](#creating-s3-bucket)
    - [Configuring Bucket Permissions](#configuring-bucket-permissions)
- [Setting Up AWS VPC](#setting-up-aws-vpc) 
    - [Creating a VPC](#creating-a-vpc)
    - [Creating Subnets](#creating-subnets)
    - [Creating an Internet Gateway](#creating-an-internet-gateway)
    - [Configuring Route Tables](#configuring-route-tables)
    - [Setting Up Security Groups](#setting-up-security-groups)
- [Setting Up AWS RDS](#setting-up-aws-rds) 
    - [Configuring RDS for Production](#configuring-rds-for-production) 
- [Deploying with AWS Lambda](#deploying-with-aws-lambda) 
    - [Setting Up Lambda layers](#setting-up-lambda-layers)
    - [Roles for lambda](#roles-for-lambda)
    - [Setting up Lambda Functions](#setting-up-lambda-functions)
- [Setting Up VPC Endpoint](#setting-up-vpc-endpoint) 
- [Automating Deployment with GitHub Actions](#automating-deployment-with-github-actions) 
    - [Setting Up the Deployment Pipeline](#setting-up-the-deployment-pipeline) 
- [What's Next](#whats-next) 
    - [Expanding Your Knowledge](#expanding-your-knowledge)
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

If you don't have  a ACCESS_KEY and a SECRET_ACCESS_KEY, you should create one in the IAM menu.

Go to IAM in the AWS console.
In the left bar click on USERS.
Create your users, if you want to assing a IAM role to this users click on give consule AWS permissions, in my case I only want the user to upload files through boto3 so is not necessary.
Attach a custom policies to this user if you do not have a group already created, for S3 i give the permission S3FullAccess.
Create the user and save the ACCESS_KEY and SECRET_ACCESS_KEY for this user

#### Creating S3 Bucket

Log in to your AWS account and go to S3 in the search panel, one you are in the panel for S3:
- Click on Create bucket.
- Enter a unique Bucket name, you can only use lowercase english letter, numbers, hyphens and dots.
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
- Search for Cloudfront in the search bar
- Click in create distribution
-  Origin Domain Name: Your S3 bucket.
-  In the option 'Origin Access' Check the option: 'Origin access control settings'.
-  Create a new OAC (Origin Access Control) if you don't have one yet. With that option cloudfront will generate a new policy to access the bucket that we'll have to manually add in the bucket permissions tab.
-  Scroll down until the option Viewer protocol policy, an select Redirect HTTP to HTTPS.
-  Because we only want to server images we can select the option 'Do not enable security protections'.
-  Click create distribution.
This is the mininum setup to use cloudfront to serve the images for our S3 bucket.
The final step is to add the policy to the bucket that we want to map. For that you should see a notification for AWS where you can copy the policy.
Click in copy policy and enter the permissions tab of your bucket, click on edit, paste and click on save this policy will allow cloudfront to access the bucket.
Wait few minutes until the distribution is setup, once is ready copy the distribution domain name and use it as a root path instead of the bucket.
You can update the code like this to work with cloudfront.
```python 
if image_file:
    try:
        content_type, _ = mimetypes.guess_type(image_file.filename)
        if content_type is None:
            content_type = 'application/octet-stream'
        # Upload the image file to S3
        s3.upload_fileobj(image_file.file, BUCKET_NAME, image_file.filename,
                    ExtraArgs={'ContentType': content_type})
        cloud_front_root = 'https://your-cloudfront-domain-name.cloudfront.net'
        image_url_path = f"{cloud_front_root}/{image_file.filename}"
        return image_url_path
    except Exception as e:
        raise HTTPException(400, f"Invalid image file {str(e)}") from e

```
With that you can access your images through cloudfront hiding your bucket name.

## Setting Up AWS VPC

#### Creating a VPC
1) Go to the search bar an type VPC.
2) Click on 'create vpc'.
3) Select VPC Only
4) Write the name that your want for your VPC in my case I write 'vpc-fastapi-lambda-rds'
5) For the part 'IPv4 CIDR block', select the network IP address block you want, in my case I use '10.0.0.0/16' because I want that every subnet have 255 host addresses (/24).
6) Scroll down and click on create vpc.

#### Creating Subnets
Is best practice to create a subnet for each AZ (Availability zone), in my case I'll need a public subnet (to connect to the internet) an a private subnet to place my RDS services.
1) In the same VPC menu, look for subnets in the left bar.
2) Click on create subnet.
3) Select the VPC recently created for you (in my case was vpc-fastapi-lambda-rds).
4) Subnet name I'll use 'public-subnet-1'
5) Choose one of the different AZ. (in my case because I'm in us-east-1, I choose the AZ us-east-1a).
6) For the IPv4 subnet CIDR block, because is the first one I will take the first octobit of the host IP for the subnets, meaning that the IP will be '10.0.1.0/24'.
7) Click on add subnet and repeat steps 4-6, until you have 2 public subnet in different AZ, and 2 private subnets in the same AZ.
In resume this is what I create.


NAME                        AZ                  IPv4 subnet CIDR block


public-subnet-1         us-east-1a                10.0.1.0/24


public-subnet-2         us-east-1b                10.0.2.0/24


private-subnet-1        us-east-1a                10.0.3.0/24


private-subnet-2        us-east-1b                10.0.4.0/24


9) Click on create subnets.
10) Once is ready, select the public ones and click on actions and select edit subnet setting.
11) Check on the option 'Enable auto-assign public IPv4 address'
12) Click save, do the same for each public subnet.

#### Creating an Internet Gateway
The archtecture for the VPC and subnets is almost done, now we need a way to interate with the world, for that we have to set up an internet gateway to allow anyone connect to the public subnet of our VPC.
1) In the same VPC menu, look for 'Internet gateway' in the left bar.
2) Click on create internet gateway.
3) Give it a name, I use 'vpc-internet-gateway'.
4) Click on create.
5) One is finished click on Action, option Atttach to VPC.
6) Select the VPC we previously created. ('vpc-fastapi-lambda-rds').

#### Configuring Route Tables
Finally we need to set up the route table for the VPC know how to handle the connections that will receive fromt the internet.
1) In the same VPC menu, look for 'route tables' in the left bar.
2) Click on create route table.
3) Give it a name that you want, I use 'vpc-fastapi-lambda-rds-route-table'
4) Select the recentrly created VPC (vpc-fastapi-lambda-rds-route-table).
5) Click on create route table.
6) Now one that route table is create click 'subnet associations'
7) Click on 'Edit subnet associations' for the 'Explicit subnet associations' tab.
8) Select the private one and click save.
9) Go back to the route tables menu, and below the recently created route table you will see the main route table (should have a '-' as a name), select this main table an go to the 'routes' tab.
10) Click on edit router and add the route '0.0.0.0/0' (everything) and target the internet gateway created previosly (vpc-internet-gateway).
11) Click save changes.
With this set up the 'MAIN' route table will have the route for internet and the public subnets.

#### Setting Up Security Groups
Let's create SG before hand for our RDS and lambda to interect between each other. Look in the left bar the option 'Security groups' in the VPC menu.

Lambda SG:
1) Click on create Security group.
2) Give it a name and description you want, I will start with a SG for lambda so I'll call it 'lambdaSG'.
3) VPC select the one that created previosly (vpc-fastapi-lambda-rds).
4) Only add the outbound rule to allow any traffic for everywhere 0.0.0.0/0
5) Click on create Security group

RDS SG:
1) Let's create another SG for RDS connection with the same VPC.
2) Add inbound rule, type: Postgresql, Source: custom and look for the lambdaSG.
3) Outbound rule, everywhere.
4) Click on create Security group.


## Setting Up AWS RDS

Go to the search bar and write RDS, one there we first need to create a new Subnet group, look up in the left bar the option for Subnet group and click on 'create DB subnet group'.
Give it a name, description and choose the VPC previously created and select only the private subnets.

#### Configuring RDS for Production

 once there click on DB instance and click on 'create database'.
I will details the steps that I made to settup a postgresql DB.
1) Select postgresql.
2) Template left it as production.
3) In 'Availability and durability' select 'Single DB instance'.
4) In the settings give it your own identifier name.
5) In credentials I decided to choose 'Self managed'
6) Enter a strong password.
7) Select the Storage type you want to use (I left the current one).
8) In connectivity Select the VPC that we previously create (vpc-fastapi-lambda-rds).
9) In DB subnet group select the db subnet group created previously.
10) Public access select 'No'.
11) For the security Group choose the one that was created previously for RDS.
12) Scroll down to additional configuration where you can set up a DB name.
13) Click on create database.

## Deploying with AWS Lambda

#### Setting Up Lambda layers
Let's install our python dependencies in a layer, because I'm on windows I'll do a work around using docker to install the packages compatible with AWS.
**Create zip file for docker**
1) Make a directory called lambda_layer, and a sub-directory lambda_layer\python (On windows)
2) With docker desktop running, run the following command:
```bash 
docker run --rm -v ${PWD}:/var/task -w /var/task public.ecr.aws/sam/build-python3.10 `
bash -c "pip install -r requirements.txt -t lambda_layer/python"
``` 
docker run: Runs a Docker container.
--rm: Automatically removes the container when it exits.
-v "%cd%":/var/task: Mounts the current directory (%cd%) to /var/task inside the container. %cd% represents the current directory in Windows.
-w /var/task: Sets the working directory inside the container to /var/task.
public.ecr.aws/sam/build-python3.10: Uses a Docker image that replicates the AWS Lambda Python 3.10 runtime environment for aws architecture x86_64.
pip install -r requirements.txt -t lambda_layer/python: Installs your dependencies into the lambda_layer/python directory.
If you are using another python version changed the 3.10 part for your current version.
Go to the folder lambda_layer\python and your should see all the packages.
3) Comprime all the files in a zip, make sure that when you unzip the file there is a root folder called python, and below that are the packages
--python
    -- module1
    -- module2
    -- rest of packages

**Create lambda Layer**
1) Look for Lambda in the search bar on AWS.
2) In th left pannel click on layers.
3) Click on create layer
4) Give it a name and a description to your layer.
5) Inn the compatible runtime option choose python 3.10.
6) Uplodad the .zip file with the packages.
7) click on create.

#### Roles for lambda
Before creating the function you'll need a few roles to access S3, RDS, cloudWatch and VPC.
Go to IAM menu, and create new roles, attach the following policies.
- AmazonCloudWatchEvidentlyFullAccess
- AmazonCloudWatchRUMFullAccess
- AmazonRDSFullAccess
- AmazonS3FullAccess
- AWSLambdaBasicExecutionRole
- AWSLambdaVPCAccessExecutionRole
- CloudWatchActionsEC2Access
- CloudWatchApplicationSignalsFullAccess
- CloudWatchEventsFullAccess

#### Setting up Lambda Functions
1) In the menu for lambda, click on functions on the left bar menu.
2) Select the option 'Author from Scratch'.
3) Give it a name that you want.
4) Runtime I use python 3.10
5) Permissions select 'use a existing role' and select the role we created the last step.
6) In additional configuration the option, turn on 'Enable VPC' and select the VPC we create before, select the public subnets, and select the Security group for lambda.
7) Click on create function.
8) One the function is created go to code tap and click the option 'Upload from' and select '.zip file'.
9) Upload the code of your app as a zip file (if you set up the layer you don't need to add the packages).
10) Now we need to change the handler function. Scroll down to runtime setting and click on edit.
11) Change the handler function to the one function that invoke the handler, in this case is 'app.handler' and click save.
12) To add the layer, scroll down to the layer tab and click on 'Add a layer'.
13) Select 'Custom layer' and choose the layer with the dependencies.
14) Click Add.

**Add Environment variables**
In your lambda function go to configuration tab and click on environment variables, and add the following variables.
- SECRET_JWT
- BUCKET_NAME
- AWS_ACCESS_KEY_FASTAPI
- AWS_SECRET_ACCESS_KEY_FASTAPI
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_HOST

**Api gateway**
To test the lambda function we can create a api gateway.
1) Go to API Gateway services.
2) Click on create endpoint.
3) Select http API.
4) Integration select lambda and the lambda function we create.
5) Click next.
6) In router, method any, and in resource path write /{proxy+} to catch all the endpoint.
7) Click next and create.
8) Test your endpoint, append the resourse path at the end.
9) Look for CloudWatch logs for any error.


## Setting Up VPC Endpoint

Our lambda function will try to upload a image to S3 bucket doing that will have to go to the public internet and send the image to S3 bucket and wait the response, this method is very slow and insecure. So, instead of going through the internet we can set a VPC endpoint to communicate our VPC with the bucket we want to upload the file with this services leveraging all the capabilities of AWS using their fast and secure private conection to S3.
1) Search for 'VPC' in the search bar in AWS.
2) In the left bar menu click on Endpoints.
3) write a name, type is AWS services.
4) And for the services look for S3 in your region (ex: com.amazonaws.us-east-1.s3). Choose the one with type Gateway (S3 must choose gateway).
5) In network settings select the VPC you want to associated
6) Select the route table associated with the subnets where lambda function is placed (Public subnets).
7) Select full access.
8) Click on create endpoint.
9) One is finished you should see the new entry in the router table with the prefix autogenerated by AWS.
10) 

## Automating Deployment with GitHub Actions

#### Setting Up the Deployment Pipeline
