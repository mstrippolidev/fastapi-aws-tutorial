from sqlalchemy import Column, Integer, String, ForeignKey
from datetime import datetime
from database.database import baseModel
from sqlalchemy.orm import relationship
# import passlib.hash

from passlib.hash import bcrypt

class User(baseModel):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    last_name = Column(String, nullable=True)
    password_hash = Column(String)
    created_at = Column(String, default=datetime.utcnow())

    # Relationships
    posts = relationship('Posts', back_populates='user') # BACK_POPULATE USE THE NAME OF THE ATTRIBUTE
                                                    # THAT MAKE REFERENCE BACKWARDS RELATIONSHIP

    def check_password(self, password:str) -> bool:
        return bcrypt.verify(password, self.password_hash)

class Posts(baseModel):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    image = Column(String, nullable=True)
    created_at = Column(String, default=datetime.utcnow())

    # relationship
    user = relationship("User", back_populates='posts')

