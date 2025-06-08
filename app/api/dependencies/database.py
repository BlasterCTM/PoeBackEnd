from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database.database import db

async def get_database() -> Generator[Session, None, None]:
    """
    Dependency to get a database session
    """
    return db.get_db()
