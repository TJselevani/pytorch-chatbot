import mysql.connector

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",      # Change if using a remote MySQL server
    user="superuser",      # Your MySQL username
    password="developer",  # Your MySQL password
    database="chatbot_db"  # The MySQL database you created
)

cursor = conn.cursor()