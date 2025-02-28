import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.create_db import create_tables
from database.db_connection import conn, cursor

def main():
    """
    Sets up the database by creating tables.
    """
    try:
        create_tables()
        conn.commit()
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
