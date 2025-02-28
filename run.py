import subprocess
import os
import sys
from config import DB_INITIALIZED_FILE, TRAINING_DATA_FILE

def main():
    """
    Runs the setup, data import, training, and app execution.
    """
    try:
        # Create a flag file to avoid re-running setup every time
        if not os.path.exists(DB_INITIALIZED_FILE):
            # Step 1: Set up the database
            print("🔹 Setting up the database...")
            subprocess.run(["python", "scripts/setup_db.py"], check=True)

            # Step 2: Import data into the database
            print("🔹 Importing data into the database...")
            subprocess.run(["python", "scripts/import_db_data.py"], check=True)

            open(DB_INITIALIZED_FILE, "w").close()
            print("✅ Database setup completed!")

        # Create a flag file to avoid re-training model every time
        if not os.path.exists(TRAINING_DATA_FILE):
            # Step 3: Train the model
            print("🔹 Training the model...")
            subprocess.run(["python", "scripts/train.py"], check=True)
            print("✅ Model Training completed!")

        # Step 4: Run the app
        print("🔹 Running the app...")
        subprocess.run(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")

if __name__ == "__main__":
    main()
