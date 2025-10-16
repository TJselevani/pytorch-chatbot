"""
Main application entry point for the hybrid chatbot system.
"""

import logging
import logging.config

from app.hybrid_chatbot import HybridChatBot
from config.settings import (
    API_CONFIG,
    LOGGING_CONFIG,
    MEMORY_CONFIG,
    PYTORCH_CONFIG,
    WORKFLOW_CONFIG,
)
from utils.memory import PersistentMemoryManager
from services.account_service import AccountService
from services.route_service import RouteService
from services.transfer_service import TransferService

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


def create_chatbot():
    """Factory function to create configured chatbot instance."""

    # Initialize persistent memory
    memory_manager = PersistentMemoryManager(MEMORY_CONFIG["sqlite_path"])

    # Initialize services
    account_service = AccountService(
        base_url=API_CONFIG["otp_service_url"], timeout=API_CONFIG["timeout"]
    )

    route_service = RouteService(
        base_url=API_CONFIG["route_service_url"], timeout=API_CONFIG["timeout"]
    )

    transfer_service = TransferService(
        base_url=API_CONFIG["booking_service_url"], timeout=API_CONFIG["timeout"]
    )

    # Create chatbot
    chatbot = HybridChatBot(
        model_path=str(PYTORCH_CONFIG["model_path"]),
        intents_path=str(PYTORCH_CONFIG["intents_path"]),
        memory_manager=memory_manager,
        account_service=account_service,
        route_service=route_service,
        transfer_service=transfer_service,
        config=WORKFLOW_CONFIG,
        bot_name="Sam",
    )

    logger.info("Chatbot initialized successfully")
    return chatbot


if __name__ == "__main__":
    # Create bot instance
    bot = create_chatbot()

    print(f"{bot.bot_name}: Hello! Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit" or user_input.lower() == "exit":
            print(f"{bot.bot_name}: Goodbye!")
            break
        response = bot.process_message("terminal_user", user_input)
        print(f"{bot.bot_name}: {response[bot.bot_name]}")
