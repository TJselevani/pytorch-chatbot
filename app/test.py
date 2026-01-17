# import sys
# import os

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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

    print("=" * 60)
    print("HYBRID CHATBOT TEST SUITE")
    print("=" * 60)

    # Test 1: OTP Workflow
    print("\n[TEST 1: OTP Workflow]")
    print("-" * 60)
    response = bot.process_message("user123", "I need an OTP code")
    print(f"Bot: {response['Sam']}\n")

    response = bot.process_message(
        "user123", "My phone is 0712345678 and fleet is SM34"
    )
    print(f"Bot: {response['Sam']}\n")

    response = bot.process_message("user123", "123456")
    print(f"Bot: {response['Sam']}\n")

    # Test 2: Booking Workflow
    print("\n[TEST 2: Booking Workflow]")
    print("-" * 60)
    response = bot.process_message("user456", "Book a ticket from Nairobi to Mombasa")
    print(f"Bot: {response['Sam']}\n")

    response = bot.process_message("user456", "1")
    print(f"Bot: {response['Sam']}\n")

    # Test 3: Transfer Workflow
    print("\n[TEST 3: Transfer Workflow]")
    print("-" * 60)
    response = bot.process_message("user789", "Transfer 500 from SM34 to SM45")
    print(f"Bot: {response['Sam']}\n")

    response = bot.process_message("user789", "yes")
    print(f"Bot: {response['Sam']}\n")

    # Test 4: Route Inquiry
    print("\n[TEST 4: Route Inquiry]")
    print("-" * 60)
    response = bot.process_message("user101", "What's the fare from Nairobi to Kisumu?")
    print(f"Bot: {response['Sam']}\n")

    print("=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
