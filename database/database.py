import sqlalchemy, os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# DB_URL = "sqlite:///./mydb.db"
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DB_URL)
# create_engine(DB_URL, connect_args={"check_same_thread": False}) if you want that different thread
# access the same db instance

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

baseModel = declarative_base()