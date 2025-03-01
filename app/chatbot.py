import os
import sys
import random
import torch
from utils.nltk_utils import bag_of_words, tokenize
from database.db_connection import conn, cursor
from models.neural_net import NeuralNet

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class ChatBot:
    def __init__(self, file_path, bot_name):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.FILE = file_path
        self.bot_name = bot_name
        self.load_model()
        self.load_intents()

    def load_model(self):
        """
        Load chatbot model from file.
        """
        data = torch.load(self.FILE)
        self.input_size = data["input_size"]
        self.hidden_size = data["hidden_size"]
        self.output_size = data["output_size"]
        self.all_words = data["all_words"]
        self.tags = data["tags"]
        self.model_state = data["model_state"]

        self.model = NeuralNet(self.input_size, self.hidden_size, self.output_size).to(self.device)
        self.model.load_state_dict(self.model_state)
        self.model.eval()

    def load_intents(self):
        """
        Fetch intents, patterns, and responses from MySQL database.
        """
        cursor.execute("SELECT id, tag FROM intents")
        intents = cursor.fetchall()

        self.intents_data = {}

        for intent_id, tag in intents:
            # Fetch patterns
            cursor.execute("SELECT pattern FROM patterns WHERE intent_id = %s", (intent_id,))
            patterns = [row[0] for row in cursor.fetchall()]

            # Fetch responses
            cursor.execute("SELECT response FROM responses WHERE intent_id = %s", (intent_id,))
            responses = [row[0] for row in cursor.fetchall()]

            self.intents_data[tag] = {"patterns": patterns, "responses": responses}

    def process_message(self, message):
        """
        Process user message and return chatbot response.
        """
        sentence = tokenize(message)
        X = bag_of_words(sentence, self.all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(self.device)

        output = self.model(X)
        _, predicted = torch.max(output, dim=1)
        tag = self.tags[predicted.item()]

        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]
        
        if prob.item() > 0.75 and tag in self.intents_data:
            response = random.choice(self.intents_data[tag]["responses"])
            return {
                "you": message,
                f"{self.bot_name}": f"{response}"
            }
        
        return {
            "you": message,
            f"{self.bot_name}": f"I do not understand..."
        }
