from fastapi import Depends
from sqlalchemy.orm import Session
from Apis.database import DBManager

db_manager = DBManager.get_instance()

def get_db() -> Session:
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


