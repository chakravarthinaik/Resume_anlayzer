import os
from dotenv import load_dotenv

load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT"))
MONGO_DB = os.getenv("MONGO_DB")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# MongoDB connection string
MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"