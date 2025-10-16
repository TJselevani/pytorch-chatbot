"""
Configuration settings for the hybrid chatbot system.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "model"

# PyTorch Model Configuration
PYTORCH_CONFIG = {
    "model_path": MODELS_DIR / "intent_model.pth",
    "intents_path": DATA_DIR / "intents.json",
    "confidence_threshold": 0.75,
    "hidden_size": 8,
    "device": "cuda" if os.getenv("USE_CUDA", "false").lower() == "true" else "cpu",
}

# Workflow Configuration
WORKFLOW_CONFIG = {
    "otp_timeout": 300,  # 5 minutes
    "booking_timeout": 600,  # 10 minutes
    "transfer_timeout": 180,  # 3 minutes
    "route_timeout": 60,  # 1 minute
    "max_retries": 3,
    "session_expiry": 1800,  # 30 minutes
    "confidence_threshold": 0.75,
}

# Memory Configuration
MEMORY_CONFIG = {
    "persist_directory": BASE_DIR / "checkpoints",
    "sqlite_path": BASE_DIR / "checkpoints" / "conversations.db",
    "cleanup_interval": 3600,  # 1 hour
}

# API Configuration
API_CONFIG = {
    "otp_service_url": os.getenv("OTP_SERVICE_URL", "http://localhost:8001"),
    "booking_service_url": os.getenv("BOOKING_SERVICE_URL", "http://localhost:8002"),
    "route_service_url": os.getenv("ROUTE_SERVICE_URL", "http://localhost:8003"),
    "timeout": 30,
}

# Language Configuration
SUPPORTED_LANGUAGES = ["en", "sw"]
DEFAULT_LANGUAGE = "en"

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "filename": BASE_DIR / "logs" / "chatbot.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "root": {"level": "INFO", "handlers": ["console", "file"]},
}


# Construct an absolute path to the data directory
DATA_DIR = os.path.join(BASE_DIR, "data")

# Define paths to important files
INTENTS_FILE = os.path.join(DATA_DIR, "intents.json")
TRAINING_DATA_FILE = os.path.join(DATA_DIR, "training_data.pth")
DB_INITIALIZED_FILE = os.path.join(DATA_DIR, "db_initialized.txt")

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "new_schema",
}

# Model configuration
MODEL_CONFIG = {
    "hidden_size": 8,
    "num_epochs": 1000,
    "batch_size": 8,
    "learning_rate": 0.001,
}


SMS_CONFIG = {
    "baseurl": "https://httpbin.org",  # "https://www.w3schools.com/python/demopage.php",
    "apiKey": "TEST_API_KEY",
    "senderID": "TESTSENDER",
}

# config.py - Add LangGraph configuration
LANGCHAIN_CONFIG = {
    "llm_provider": "anthropic",  # or "openai"
    "model_name": "claude-3-haiku-20240307",  # cost-effective for workflows
    "api_key": "your-api-key-here",
    "temperature": 0.1,  # Low temperature for consistent workflow behavior
    "max_tokens": 1000,
}
