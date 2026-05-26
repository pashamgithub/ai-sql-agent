import os
from dotenv import load_dotenv

# Load .env from backend root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")

load_dotenv(ENV_PATH)
class Settings:
    DB_PATH = os.getenv("DB_PATH")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
settings = Settings()
