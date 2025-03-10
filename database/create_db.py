import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_connection import cursor
from config import DB_CONFIG


def create_tables():
    """
    Drops the existing database (if it exists) and creates a fresh one with necessary tables.
    """

    # Drop database if it exists
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")

    # Create a fresh database
    cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
    cursor.execute(f"USE {DB_CONFIG['database']}")

    # Create a table for intents
    cursor.execute(
        """
        CREATE TABLE intents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tag VARCHAR(255) UNIQUE NOT NULL,
            category VARCHAR(255) NOT NULL,
            context VARCHAR(255),
            language VARCHAR(255)
        )
        """
    )

    # Create a table for patterns
    cursor.execute(
        """
        CREATE TABLE patterns (
            id INT AUTO_INCREMENT PRIMARY KEY,
            intent_id INT NOT NULL,
            pattern TEXT NOT NULL,
            FOREIGN KEY (intent_id) REFERENCES intents(id) ON DELETE CASCADE
        )
        """
    )

    # Create a table for responses
    cursor.execute(
        """
        CREATE TABLE responses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            intent_id INT NOT NULL,
            response TEXT NOT NULL,
            FOREIGN KEY (intent_id) REFERENCES intents(id) ON DELETE CASCADE
        )
        """
    )

    print("✅ Database reset and tables created successfully!")


if __name__ == "__main__":
    create_tables()
