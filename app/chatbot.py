import os
import sys
import random
import torch

from utils.nltk_utils import bag_of_words, tokenize
from database.db_connection import cursor
from models.neural_net import NeuralNet
from utils.handlers.driver_request import handle_driver_request
from utils.handlers.passenger_request import handle_passenger_request
from utils.match import detect_language
from lib.logger import Logger

logger = Logger(name="chatbot", create_separate_log=True)

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class ChatBot:
    def __init__(self, file_path, bot_name="Sam"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.FILE = file_path
        self.bot_name = bot_name
        self.load_model()
        self.load_intents()

    def load_model(self):
        """Load chatbot model from file."""
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
        """Fetch intents, patterns, and responses from MySQL database."""
        cursor.execute("SELECT id, tag FROM intents")
        intents = cursor.fetchall()
        self.intents_data = {}

        for intent_id, tag in intents:
            cursor.execute("SELECT pattern FROM patterns WHERE intent_id = %s", (intent_id,))
            patterns = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT response FROM responses WHERE intent_id = %s", (intent_id,))
            responses = [row[0] for row in cursor.fetchall()]

            self.intents_data[tag] = {"patterns": patterns, "responses": responses}
    

    def process_message(self, user_id, message):
        """Processes the user message and returns chatbot response."""
         # Detect language of the message
        language = detect_language(message)

        # If no special handling, proceed with intent classification
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
            possible_responses = self.intents_data[tag]["responses"]
            
            # Prioritize responses containing words from the user's input
            user_words = set(message.lower().split())
            matched_responses = [resp for resp in possible_responses if any(word in resp.lower() for word in user_words)]

            # If there are matched responses, choose one; otherwise, pick randomly
            response = random.choice(matched_responses) if matched_responses else random.choice(possible_responses)
        else:
            # Provide both English and Swahili responses
            response_map = {
                "en": "I do not understand. Could you please clarify?",
                "sw": "Sielewi. Tafadhali fafanua."
            }
            
            response = response_map.get(language, response_map["en"]) 

        # First, check for OTP and transfer-related messages
        special_response = handle_driver_request(self.bot_name, user_id, message, response)
        if special_response:
            return special_response

        # Second, check for OTP and transfer-related messages
        # special_response = handle_passenger_request(self.bot_name, user_id, message)
        # if special_response:
        #     return special_response

        # Third return the bot's message
        return {self.bot_name: response}

        
    def chat_terminal(self):
        """Run chatbot in terminal mode."""
        print(f"{self.bot_name}: Hello! Type 'quit' to exit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == "quit":
                print(f"{self.bot_name}: Goodbye!")
                break
            response = self.process_message("terminal_user", user_input)
            print(f"{self.bot_name}: {response[self.bot_name]}")
