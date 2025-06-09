from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database.database import db

def get_database() -> Generator[Session, None, None]:
    """
    Dependency to get a database session
    """
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
