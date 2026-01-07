import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Use DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and "pgbouncer=true" in DATABASE_URL:
    # Remove pgbouncer parameter for compatibility with psycopg2
    DATABASE_URL = DATABASE_URL.replace("?pgbouncer=true", "").replace("&pgbouncer=true", "")

if not DATABASE_URL:
    # Fallback for local development if no .env is found
    DATABASE_URL = "sqlite:///./top_players.db"

# Create Database Engine
engine = create_engine(DATABASE_URL)

# Create Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
