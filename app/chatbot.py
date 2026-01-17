"""
Base PyTorch chatbot for intent classification.
This is your existing chatbot that the hybrid system extends.
"""

import json
import logging
import random
import torch

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nn.neural_network import NeuralNet
from config.settings import PYTORCH_CONFIG
from utils.language import detect_language
from database.db_connection import cursor


logger = logging.getLogger(__name__)


class ChatBot:
    """Hybrid PyTorch chatbot using both DB and JSON intents with intelligent response matching."""

    def __init__(self, model_path, intents_path, bot_name="Sam"):
        self.bot_name = bot_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load model
        self._load_model(model_path)

        # Load intents (DB preferred, fallback to JSON)
        try:
            self.load_intents_from_db()
            logger.info("Loaded intents from database.")
        except (RuntimeError, ConnectionError, TimeoutError, ValueError) as e:
            logger.warning(f"DB intents load failed: {e}, falling back to JSON.")
            self.load_intents_from_json(intents_path)

        logger.info("ChatBot '%s' initialized on %s", bot_name, self.device)

    # -------------------------
    # Loading Model & Intents
    # -------------------------
    def _load_model(self, model_path):
        """Load trained PyTorch model from file."""
        data = torch.load(model_path, map_location=self.device)
        self.input_size = data["input_size"]
        self.hidden_size = data["hidden_size"]
        self.output_size = data["output_size"]
        self.all_words = data["all_words"]
        self.tags = data["tags"]
        model_state = data["model_state"]

        self.model = NeuralNet(self.input_size, self.hidden_size, self.output_size).to(
            self.device
        )
        self.model.load_state_dict(model_state)
        self.model.eval()

        logger.info(
            f"Model loaded: {len(self.tags)} intents, {len(self.all_words)} words"
        )

    def load_intents_from_json(self, intents_path):
        """Fallback: Load intents from JSON file."""
        with open(intents_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.intents_data = {
            intent["tag"]: {
                "patterns": intent["patterns"],
                "responses": intent["responses"],
            }
            for intent in data["intents"]
        }

    def load_intents_from_db(self):
        """Fetch intents, patterns, and responses from MySQL database."""
        cursor.execute("SELECT id, tag FROM intents")
        intents = cursor.fetchall()
        if not intents:
            raise ValueError("No intents found in database")

        self.intents_data = {}
        for intent_id, tag in intents:
            cursor.execute(
                "SELECT pattern FROM patterns WHERE intent_id = %s", (intent_id,)
            )
            patterns = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                "SELECT response FROM responses WHERE intent_id = %s", (intent_id,)
            )
            responses = [row[0] for row in cursor.fetchall()]

            self.intents_data[tag] = {"patterns": patterns, "responses": responses}

    # -------------------------
    # Core Message Processing
    # -------------------------

    def process_message(self, user_id, message):
        """
        Process message and return response.
        This is the method that HybridChatBot will override.
        """
        from utils.nltk_utils import tokenize, bag_of_words

        # Tokenize and create bag of words
        sentence = tokenize(message)
        X = bag_of_words(sentence, self.all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(self.device)

        # Get prediction
        output = self.model(X)
        _, predicted = torch.max(output, dim=1)
        tag = self.tags[predicted.item()]

        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]

        # Find response for tag
        # Confidence check
        if prob.item() > 0.75 and tag in self.intents_data:
            intent_data = self.intents_data[tag]
            possible_responses = intent_data["responses"]

            # Find responses that contain user words
            user_words = set(message.lower().split())
            matched_responses = [
                resp
                for resp in possible_responses
                if any(word in resp.lower() for word in user_words)
            ]

            response = (
                random.choice(matched_responses)
                if matched_responses
                else random.choice(possible_responses)
            )
        else:
            # Default fallback with language detection
            language = detect_language(message)
            response = {
                "en": "I'm not sure I understand. Could you rephrase that?",
                "sw": "Sielewi vizuri. Tafadhali fafanua.",
            }.get(language, "I'm not sure I understand.")

        return {self.bot_name: response}

    # -------------------------
    # Terminal Chat Interface
    # -------------------------
    def chat_terminal(self):
        print(f"{self.bot_name}: Hello! Type 'quit' to exit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["quit", "exit"]:
                print(f"{self.bot_name}: Goodbye!")
                break
            response = self.process_message("terminal_user", user_input)
            print(f"{self.bot_name}: {response[self.bot_name]}")


def main():
    chatbot = ChatBot(
        model_path=PYTORCH_CONFIG["model_path"],
        intents_path=PYTORCH_CONFIG["intents_path"],
        bot_name="ai-app",
    )

    chatbot.chat_terminal()


if __name__ == "__main__":
    main()
