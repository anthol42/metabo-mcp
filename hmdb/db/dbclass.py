import sqlite3
from contextlib import contextmanager

class DBClass:
    @contextmanager
    def cursor(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()