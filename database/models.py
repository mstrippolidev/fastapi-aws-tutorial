"""
    This file contains the models that represent each table in the database for 
    user and post.
"""
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
    # Relationships BACK_POPULATE USE THE NAME OF THE ATTRIBUTE
    # THAT MAKE REFERENCE BACKWARDS RELATIONSHIP
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



class RefreshToken(baseModel): # pylint: disable=too-few-public-methods
    """
        Model for refresh token table
    """
    __tablename__ = 'refresh_token'
    id = Column(Integer, primary_key=True, index=True)
    refresh_token = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    created_at = Column(String, default=datetime.now(timezone.utc))
