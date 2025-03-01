import random
import torch
import mysql.connector
from utils.nltk_utils import bag_of_words, tokenize
from database.db_connection import conn, cursor
from config import TRAINING_DATA_FILE
from models.neural_net import NeuralNet

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load model data
FILE = TRAINING_DATA_FILE #"data/training_data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

# Load intents from MySQL database
cursor.execute("SELECT id, tag FROM intents")
intents = cursor.fetchall()

intents_data = {}

for intent_id, tag in intents:
    # Fetch patterns
    cursor.execute("SELECT pattern FROM patterns WHERE intent_id = %s", (intent_id,))
    patterns = [row[0] for row in cursor.fetchall()]

    # Fetch responses
    cursor.execute("SELECT response FROM responses WHERE intent_id = %s", (intent_id,))
    responses = [row[0] for row in cursor.fetchall()]

    intents_data[tag] = {"patterns": patterns, "responses": responses}

bot_name = "Sam"
print("Let's chat! (type 'quit' to exit)")
while True:
    # sentence = "do you use credit cards?"
    sentence = input("You: ")
    if sentence == "quit":
        break

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
        print(f"{bot_name}: {random.choice(intents_data[tag]['responses'])}")
    else:
        print(f"{bot_name}: I do not understand...")
