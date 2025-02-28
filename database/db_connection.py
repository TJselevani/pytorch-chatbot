import mysql.connector
from config import DB_CONFIG

# Create database connection
conn = mysql.connector.connect(
    host=DB_CONFIG["host"],
    user=DB_CONFIG["user"],
    password=DB_CONFIG["password"],
    database=DB_CONFIG["database"]
)

# Create cursor
cursor = conn.cursor()