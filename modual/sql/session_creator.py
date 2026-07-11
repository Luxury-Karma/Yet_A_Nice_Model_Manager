"""
@Project: modual/sql/session_creator.py
@Author: Alexandre Gauvin
This file is holding the sql session creator.
"""

from os import makedirs
from os.path import dirname, join, abspath, exists
from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

TARGET_DIR:str = join(dirname(abspath(__file__)), 'database')

if not exists(TARGET_DIR):
    print(f"📁 Creating missing database directory structure at: {TARGET_DIR}")
    makedirs(TARGET_DIR, exist_ok=True)

DB_URL: str = f'sqlite:///{join(TARGET_DIR, "library.db")}'

tag_DB_URL : str = f'sqlite:///{join(TARGET_DIR, "tag.db")}'

print(f'🔗 Model database file absolute path: {join(TARGET_DIR, "library.db")}')
print(f'🔗 Tag database file absolute path: {join(TARGET_DIR, "library.db")}')

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
tag_engine = create_engine(tag_DB_URL, connect_args={"check_same_thread": False})

session_local = sessionmaker(bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, Any, None]:
    """
    Create a temporary database for an operation and then close it.
    :return: sql database session
    """
    db = session_local()
    try:
        yield db
    finally:
        db.close()
