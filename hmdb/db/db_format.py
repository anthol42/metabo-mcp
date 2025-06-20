import sqlite3
import os
from pathlib import Path
from typing import List, Union

root = Path(__file__).parent

def create_db(db_path: Union[str, Path]) -> None:
    """Create the database schema for HMDB."""
    if os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the metabolites table
    with open(root / "schema.sql", "r") as f:
        schema = f.read()

    # Create the database schema
    cursor.executescript(schema)


    conn.commit()
    conn.close()

