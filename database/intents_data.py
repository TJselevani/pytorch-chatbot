import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db_connection import cursor

cursor.execute(
    """
    SELECT intents.id, intents.tag, patterns.pattern
    FROM intents
    JOIN patterns ON intents.id = patterns.intent_id
"""
)
data = cursor.fetchall()

intents_dict = {}
for intent_id, tag, pattern in data:
    if tag not in intents_dict:
        intents_dict[tag] = {"id": intent_id, "patterns": []}
    intents_dict[tag]["patterns"].append(pattern)

# Convert to lists
intents = [
    {"tag": tag, "patterns": details["patterns"]}
    for tag, details in intents_dict.items()
]
