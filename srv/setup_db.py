import subprocess

print("🔹 Creating database tables...")
subprocess.run(["python", "database.create_db.py"])

print("🔹 Inserting intents data into database...")
subprocess.run(["python", "database.create_db_data.py"])

print("✅ Database setup complete!")
