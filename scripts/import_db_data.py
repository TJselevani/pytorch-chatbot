import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from database.create_data import load_data_into_db
from database.db_connection import conn, cursor
from config import DB_INITIALIZED_FILE

def main():
    """
    Imports data from intents.json into the database.
    """
    try:
        load_data_into_db()
        conn.commit()
        print("Data imported into database successfully.")

        # Mark database as initialized
        with open(DB_INITIALIZED_FILE, "w") as f:
            f.write("initialized")

    except Exception as e:
        print(f"Error importing data into database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
