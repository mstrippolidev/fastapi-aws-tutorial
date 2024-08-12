from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    name: str
    
class UserCreate(UserBase):
    password: str
    last_name: Optional[str]

    class Config:
        from_attributes = True # Allow the pydantic model to read the lazy-data from sqlAlchemy  

class UserResponse(UserBase):
    id: int
    created_at: datetime
    last_name: Optional[str] = None

    class Config:
        from_attributes = True



class PostsBase(BaseModel):
    title: str
    content: str


class PostCreate(PostsBase):
    pass
    class Config:
        from_attributes = True

class PostCreateImage(PostsBase):
    image_str:Optional[str] = None
    image_b64: Optional[str] = None


class PostResponse(PostsBase):
    id: int
    created_at: str
    user_id: int
    image: Optional[str]

    class Config:
        from_attributes = True


class PostResponseUser(PostResponse):
    user: UserResponse


class ResponsePaginated(BaseModel):
    page: int
    total_pages: int
    total: int
    
    
class PostResponsePaginated(ResponsePaginated):
    data: List[PostResponse]
    class Config:
        from_attributes = True
