import subprocess
import os
import sys
import signal
from config import DB_INITIALIZED_FILE, TRAINING_DATA_FILE

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))


def signal_handler(sig, frame):
    """Handler for SIGINT signal."""
    print("\n🔴 Received SIGINT, terminating processes...")
    # Terminate any running subprocesses here if needed
    sys.exit(0)


def main():
    """
    Runs the setup, data import, training, and app execution.
    """
    try:
        # Register SIGINT handler
        signal.signal(signal.SIGINT, signal_handler)

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
        # Use subprocess.Popen instead of subprocess.run for more control
        app_process = subprocess.Popen(
            [
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload",
            ]
        )

        # Wait for the app process to finish
        try:
            app_process.wait()
        except KeyboardInterrupt:
            print("\n🔴 Received SIGINT, terminating app process...")
            app_process.terminate()
            app_process.wait()  # Wait for the process to terminate

    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")


if __name__ == "__main__":
    main()
