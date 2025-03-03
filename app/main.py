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
    user_id: str  # Unique identifier for the user
    message: str

@app.post("/chat/")
def chat(user_message: UserMessage):
    """API endpoint to process user message."""
    return chatbot.process_message(user_message.user_id, user_message.message)
