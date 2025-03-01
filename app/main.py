# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from .chatbot import ChatBot
from config import TRAINING_DATA_FILE

app = FastAPI()

# Initialize chatbot
bot_name = "Sam"
file_path = TRAINING_DATA_FILE
chatbot = ChatBot(file_path, bot_name)

# Pydantic model for input validation
class UserMessage(BaseModel):
    message: str

@app.post("/chat/")
def chat(user_message: UserMessage):
    """
    Process user message and return chatbot response.
    """
    return chatbot.process_message(user_message.message)
