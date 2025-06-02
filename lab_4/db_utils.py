import sqlite3
import logging
from functools import wraps

DB_PATH = "banking.db"

def db_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            result = func(cursor, *args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            logging.error(f"Error in {func.__name__}: {e}")
            raise
        finally:
            conn.close()
    return wrapper
