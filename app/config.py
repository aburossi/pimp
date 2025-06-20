# app/config.py

import os
from dotenv import load_dotenv

def load_api_keys():
    """
    Loads API keys from a .env file into environment variables.
    It's best practice to call this once at the start of the application.
    """
    load_dotenv()
    # You can add checks here to ensure keys are present
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found in .env file.")
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Warning: GOOGLE_API_KEY not found in .env file.")