from .db_connection import cursor, conn
from config import DB_CONFIG

def create_tables():
    """
    Creates the necessary tables in the database.
    """

    # Create database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    cursor.execute(f"USE {DB_CONFIG['database']}")
    
    # Create a table for intents
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS intents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tag VARCHAR(255) UNIQUE NOT NULL
    )
    ''')

    # Create a table for patterns
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patterns (
        id INT AUTO_INCREMENT PRIMARY KEY,
        intent_id INT NOT NULL,
        pattern TEXT NOT NULL,
        FOREIGN KEY (intent_id) REFERENCES intents(id) ON DELETE CASCADE
    )
    ''')

    # Create a table for responses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS responses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        intent_id INT NOT NULL,
        response TEXT NOT NULL,
        FOREIGN KEY (intent_id) REFERENCES intents(id) ON DELETE CASCADE
    )
    ''')
