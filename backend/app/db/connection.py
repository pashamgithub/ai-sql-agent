import sqlite3  
from app.config import settings

def get_connection():
    return sqlite3.connect(settings.DB_PATH, check_same_thread=False)