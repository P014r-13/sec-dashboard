import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = 60
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), "db", "vault.db")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))