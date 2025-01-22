import os
from dotenv import load_dotenv

def load_env():
    """Loads environment variables from .env file"""
    load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
