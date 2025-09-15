from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres123@localhost:5432/eduaidb")

# Increase pool size and timeout to handle more concurrent connections
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Increased from default 5
    max_overflow=20,  # Increased from default 10
    pool_timeout=60,  # Increased from default 30
    pool_recycle=3600  # Recycle connections after 1 hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)
