import os

# Determine the project root directory
# Assuming this script is in the root of your project
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Construct an absolute path to the data directory
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Define paths to important files
INTENTS_FILE = os.path.join(DATA_DIR, "intents.json")
TRAINING_DATA_FILE = os.path.join(DATA_DIR, "training_data.pth")
DB_INITIALIZED_FILE = os.path.join(DATA_DIR, "db_initialized.txt")

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "superuser",
    "password": "developer",
    "database": "temp_db"
}

# Model configuration
MODEL_CONFIG = {
    "hidden_size": 8,
    "num_epochs": 1000,
    "batch_size": 8,
    "learning_rate": 0.001
}
