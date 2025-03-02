import os
from dotenv import load_dotenv, find_dotenv, dotenv_values
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Find and load the .env file directly
env_path = find_dotenv(usecwd=True)
if not env_path:
    env_path = Path(__file__).resolve().parent.parent / ".env"

print(f"Loading environment from: {env_path}")

# Get API key directly from .env file to avoid system environment variable
env_vars = dotenv_values(env_path)
OPENAI_API_KEY = env_vars.get("OPENAI_API_KEY")

# Only load from environment if not found in .env
if not OPENAI_API_KEY:
    print("API key not found in .env file, checking environment variables...")
    # Now load environment variables for other settings
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY:
    # Print the masked key for debugging
    masked_key = f"{OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-4:]}"
    print(f"Using OpenAI API key: {masked_key}")
else:
    print(
        "WARNING: OPENAI_API_KEY not found in either .env file or environment variables."
    )

# LLM Configuration
LLM_MODEL = "gpt-3.5-turbo"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 500

# Vector Database Configuration
VECTOR_DB_PATH = BASE_DIR / "data" / "vector_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Data Configuration
COCKTAILS_CSV_PATH = BASE_DIR / "data" / "cocktails.csv"

# Memory Configuration
USER_MEMORY_PATH = BASE_DIR / "data" / "user_memory"

# Application Configuration
DEBUG = True
