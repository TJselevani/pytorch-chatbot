import mysql.connector

from config import settings

# Create DB connection
conn = mysql.connector.connect(
    host=settings.db_host,
    port=settings.db_port,
    user=settings.db_user,
    password=settings.db_password,
    database=settings.db_database,
)

# Create cursor
cursor = conn.cursor()
