"""
    Pydanctic models for users, post and tokens
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel): # pylint: disable=too-few-public-methods
    """
        User base pydantic model
    """
    email: EmailStr
    name: str

class UserCreate(UserBase): # pylint: disable=too-few-public-methods
    """
        Pydanctic to handle the user created data
    """
    password: str
    last_name: Optional[str]

    class Config: # pylint: disable=too-few-public-methods
        """
            Config class
        """
        from_attributes = True # Allow the pydantic model to read the lazy-data from sqlAlchemy

class UserResponse(UserBase): # pylint: disable=too-few-public-methods
    """
        Pydantic model to response a user instance
    """
    id: int
    created_at: datetime
    last_name: Optional[str] = None

    class Config: # pylint: disable=too-few-public-methods
        """
            Configuration class
        """
        from_attributes = True

class PostsBase(BaseModel): # pylint: disable=too-few-public-methods
    """
        Post base class
    """
    title: str
    content: str

class PostCreate(PostsBase): # pylint: disable=too-few-public-methods
    """
        Pydanctic to create a post
    """
    class Config: # pylint: disable=too-few-public-methods
        """
            Config class
        """
        from_attributes = True

class PostCreateImage(PostsBase): # pylint: disable=too-few-public-methods
    """
        Save a post
    """
    image_str:Optional[str] = None
    image_b64: Optional[str] = None

class PostResponse(PostsBase): # pylint: disable=too-few-public-methods
    """
        Post response
    """
    id: int
    created_at: str
    user_id: int
    image: Optional[str]

    class Config: # pylint: disable=too-few-public-methods
        """
            Config class
        """
        from_attributes = True

class PostResponseUser(PostResponse): # pylint: disable=too-few-public-methods
    """
        Post response with user data
    """
    user: UserResponse

class ResponsePaginated(BaseModel): # pylint: disable=too-few-public-methods
    """
        Response paginated
    """
    page: int
    total_pages: int
    total: int

class PostResponsePaginated(ResponsePaginated): # pylint: disable=too-few-public-methods
    """
        Post response paginated
    """
    data: List[PostResponse]
    class Config: # pylint: disable=too-few-public-methods
        """
            Config class
        """
        from_attributes = True

class Token(BaseModel): # pylint: disable=too-few-public-methods
    """
        Pydanctic base token class
    """
    access_token:str
    refresh_token:str
    token_type:str
