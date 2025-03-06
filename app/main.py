from fastapi import FastAPI
from pydantic import BaseModel
from app.chatbot import ChatBot
from config import TRAINING_DATA_FILE

app = FastAPI()

# Initialize chatbot
BOT_NAME = "Sam"
file_path = TRAINING_DATA_FILE
chatbot = ChatBot(file_path, BOT_NAME)


# Pydantic model for input validation
class UserMessage(BaseModel):
    """Represents a user message with attached data."""

    user_id: str  # Unique identifier for the user
    message: str


@app.post("/chat/")
def chat(user_message: UserMessage):
    """API endpoint to process user message."""
    return chatbot.process_message(user_message.user_id, user_message.message)
