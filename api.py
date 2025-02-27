import random
import torch

from fastapi import FastAPI
from pydantic import BaseModel

from model import NeuralNet
from nltk_utils import bag_of_words, tokenize
from database.db_connection import conn, cursor

print(torch.__version__)

# Initialize FastAPI
app = FastAPI()

# Load chatbot model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "Sam"

# Pydantic model for input validation
class UserMessage(BaseModel):
    message: str

def fetch_intents_from_db():
    """
    Fetch intents, patterns, and responses from MySQL database.
    """
    cursor.execute("SELECT id, tag FROM intents")
    intents = cursor.fetchall()

    intent_dict = {}

    for intent_id, tag in intents:
        # Fetch patterns
        cursor.execute("SELECT pattern FROM patterns WHERE intent_id = %s", (intent_id,))
        patterns = [row[0] for row in cursor.fetchall()]

        # Fetch responses
        cursor.execute("SELECT response FROM responses WHERE intent_id = %s", (intent_id,))
        responses = [row[0] for row in cursor.fetchall()]

        intent_dict[tag] = {"patterns": patterns, "responses": responses}

    return intent_dict

# Load intents from database
intents_data = fetch_intents_from_db()

@app.post("/chat/")
def chat(user_message: UserMessage):
    """
    Process user message and return chatbot response.
    """
    sentence = user_message.message
    sentence = tokenize(sentence)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    
    if prob.item() > 0.75 and tag in intents_data:
        response = random.choice(intents_data[tag]["responses"])
        return {
            "you": user_message.message,
            f"{bot_name}": f"{response}"
        }
    
    return {
        "you": user_message.message,
        f"{bot_name}": f"I do not understand..."
    }

