import sqlite3



def create_db(db_path: str) -> None:
    """Create the database schema for HMDB."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the metabolites table
    cursor.execute(...)


    conn.commit()
    conn.close()