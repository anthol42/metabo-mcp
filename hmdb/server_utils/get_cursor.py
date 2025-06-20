import sqlite3
from .functional import regexp

class GetCursor:
    def __init__(self, db_path="db/hmdb.db"):
        self.db_path = db_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.create_function("REGEXP", 2, regexp)
        self.cursor = self.conn.cursor()
        return self.cursor  # returned to `as cursor`

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()