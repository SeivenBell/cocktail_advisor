# Modified test_env.py or api_key_test.py
import os
from dotenv import load_dotenv
import pathlib

# Print the current working directory
print(f"Current working directory: {os.getcwd()}")

# Attempt to load .env file
print("Attempting to load .env file...")
load_dotenv()

# Check if the API key is loaded
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    # Show first 5 and last 4 characters, masking the middle
    masked_key = f"{openai_key[:5]}...{openai_key[-4:]}"
    print(f"OpenAI API key found: {masked_key}")
else:
    print("OpenAI API key NOT found!")

# Try to locate the .env file
possible_locations = [
    ".env",
    "../.env",
    "../../.env",
    os.path.join(pathlib.Path(__file__).parent.absolute(), ".env"),
    os.path.join(pathlib.Path(__file__).parent.parent.absolute(), ".env"),
]

print("\nChecking for .env file in possible locations:")
for location in possible_locations:
    file_path = os.path.abspath(location)
    if os.path.exists(file_path):
        print(f"✓ Found at: {file_path}")
        # Print the content to verify it has the right structure
        try:
            with open(file_path, "r") as f:
                content = f.read()
                # Check if it contains the OpenAI API key
                if "OPENAI_API_KEY" in content:
                    # Extract the API key part
                    start_index = content.find("OPENAI_API_KEY=") + len(
                        "OPENAI_API_KEY="
                    )
                    end_index = (
                        content.find("\n", start_index)
                        if "\n" in content[start_index:]
                        else len(content)
                    )
                    key_value = content[start_index:end_index].strip()
                    # Show first 5 and last 4 characters of the key in the file
                    if len(key_value) > 10:
                        masked_file_key = f"{key_value[:5]}...{key_value[-4:]}"
                        print(f"  - OPENAI_API_KEY in file: {masked_file_key}")
                    else:
                        print(f"  - OPENAI_API_KEY in file: {key_value}")
                else:
                    print("  - OPENAI_API_KEY not found in file")
        except Exception as e:
            print(f"  - Error reading file: {e}")
    else:
        print(f"✗ Not found at: {file_path}")

print("\nEnvironment variables related to API keys:")
for key in os.environ:
    if "API_KEY" in key:
        value = os.environ[key]
        if value and len(value) > 10:
            # Show first 5 and last 4 characters for security
            masked_env_key = f"{value[:5]}...{value[-4:]}"
            print(f"- {key}: {masked_env_key}")
        else:
            print(f"- {key}: {value if value else '<empty>'}")
