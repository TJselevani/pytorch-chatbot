import json
from db_connection import cursor, conn

# Load JSON data
with open("intents.json", "r") as f:
    intents_data = json.load(f)

for intent in intents_data["intents"]:
    tag = intent["tag"]

    # Insert tag into `intents` table
    cursor.execute("INSERT IGNORE INTO intents (tag) VALUES (%s)", (tag,))
    
    # Get the intent_id
    cursor.execute("SELECT id FROM intents WHERE tag = %s", (tag,))
    intent_id = cursor.fetchone()[0]

    # Insert patterns into `patterns` table
    for pattern in intent["patterns"]:
        cursor.execute("INSERT INTO patterns (intent_id, pattern) VALUES (%s, %s)", (intent_id, pattern))

    # Insert responses into `responses` table
    for response in intent["responses"]:
        cursor.execute("INSERT INTO responses (intent_id, response) VALUES (%s, %s)", (intent_id, response))

# Commit and close connection
conn.commit()
conn.close()
