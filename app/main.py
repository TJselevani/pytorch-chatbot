# main.py


from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from app.chatbot import ChatBot
from app.request_logging import configure_logging, install_request_logging
from config import settings

configure_logging(log_file=Path("logs/requests.log"))

TRAINING_DATA_FILE = settings.training_data_file

app = FastAPI()
install_request_logging(app)

# Initialize chatbot
bot_name = "Sam"
file_path = TRAINING_DATA_FILE
chatbot = ChatBot(file_path, bot_name)

# Pydantic model for input validation
class UserMessage(BaseModel):
    message: str

@app.post("/chat/")
def chat(user_message: UserMessage):
    """API endpoint to process user message."""
    return chatbot.process_message(user_message.message)
