#!/usr/bin/env python3
"""
Script to diagnose OpenAI API issues, including rate limits and quota problems.
This script performs several tests to help determine the exact nature of API access issues.
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import argparse

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from app.config import OPENAI_API_KEY

# For direct API access
from openai import OpenAI, OpenAIError

# Load environment variables
load_dotenv()


def get_api_key():
    """Get the OpenAI API key from environment variables or config"""
    api_key = OPENAI_API_KEY

    # If no key found in app config, try environment directly
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set in your environment or .env file.")
        print(
            "Please add your OpenAI API key to the .env file in the project root directory."
        )
        print("Example: OPENAI_API_KEY=sk-your-api-key")
        return None

    return api_key


def test_api_info(api_key):
    """Get information about the API key and organization"""
    try:
        client = OpenAI(api_key=api_key)

        # Test a simple model list call to verify key works for basic operations
        models = client.models.list()

        print(f"✓ API key is valid (first 5 chars: {api_key[:5]}...)")
        print(f"✓ Successfully connected to OpenAI API")
        print(f"✓ Available models: {len(models.data)} models")

        # List a few models as examples
        print("Sample available models:")
        for model in models.data[:5]:  # Just show first 5
            print(f"  - {model.id}")

        return True
    except OpenAIError as e:
        print(f"✗ API key validation failed: {e}")
        return False


def test_simple_completion(api_key):
    """Test a simple completion to verify basic functionality"""
    try:
        client = OpenAI(api_key=api_key)

        print("\nTesting simple chat completion...")

        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": "Hello, this is a test message. Please respond briefly.",
                },
            ],
            max_tokens=20,
        )
        elapsed_time = time.time() - start_time

        print(f"✓ Simple completion succeeded in {elapsed_time:.2f} seconds")
        print(f'✓ Response: "{response.choices[0].message.content}"')
        print(f"✓ Completion tokens: {response.usage.completion_tokens}")
        print(f"✓ Prompt tokens: {response.usage.prompt_tokens}")
        print(f"✓ Total tokens: {response.usage.total_tokens}")
        return True
    except OpenAIError as e:
        print(f"✗ Simple completion failed: {e}")
        if "quota" in str(e).lower() or "rate limit" in str(e).lower():
            print("\n! This confirms you are experiencing rate limit or quota issues")
        return False


def test_rate_limits(api_key, num_requests=5, delay=0.5):
    """Test rate limits by making several rapid requests"""
    success_count = 0
    print(
        f"\nTesting rate limits with {num_requests} rapid requests (delay={delay}s)..."
    )

    try:
        client = OpenAI(api_key=api_key)

        for i in range(num_requests):
            try:
                print(f"  Request {i+1}/{num_requests}... ", end="", flush=True)
                start_time = time.time()

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": f"Test message {i+1}. Respond with one word.",
                        },
                    ],
                    max_tokens=5,
                )

                elapsed_time = time.time() - start_time
                success_count += 1
                print(
                    f'success ({elapsed_time:.2f}s) - "{response.choices[0].message.content}"'
                )

                if i < num_requests - 1:
                    time.sleep(delay)  # Add delay between requests

            except OpenAIError as e:
                print(f"failed - {e}")
                if "rate limit" in str(e).lower():
                    print(
                        "\n! Hit a rate limit. This indicates you're making too many requests too quickly."
                    )
                    print(
                        f"! Consider increasing the delay between requests (currently {delay}s)"
                    )
                    break
                elif "quota" in str(e).lower():
                    print(
                        "\n! Hit a quota limit. This indicates you've used all your available quota."
                    )
                    break

        if success_count == num_requests:
            print(f"\n✓ All {num_requests} rapid requests succeeded")
            print("✓ You do not appear to be hitting short-term rate limits")
        else:
            print(f"\n! Only {success_count}/{num_requests} requests succeeded")

        return success_count == num_requests
    except Exception as e:
        print(f"✗ Rate limit test failed with unexpected error: {e}")
        return False


def test_model_access(api_key):
    """Test access to different models to check tier permissions"""
    print("\nTesting access to different models...")

    models_to_test = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]

    client = OpenAI(api_key=api_key)

    for model in models_to_test:
        try:
            print(f"  Testing access to {model}... ", end="", flush=True)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Respond with just the word 'success'"},
                ],
                max_tokens=5,
            )

            print(f'success - "{response.choices[0].message.content}"')
        except OpenAIError as e:
            print(f"failed - {e}")
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                print(
                    f"  ! The model {model} does not exist or is not accessible with your API key"
                )
            elif "quota" in str(e).lower():
                print(f"  ! You've exceeded your quota for the {model} model")
            elif "not authorized" in str(e).lower() or "permission" in str(e).lower():
                print(
                    f"  ! Your API key does not have permission to use the {model} model"
                )


def check_key_type(api_key):
    """Try to determine what type of API key this is based on behavior"""
    # This is a heuristic check since OpenAI doesn't expose this info directly
    print("\nAttempting to determine API key type...")

    # Method 1: Key prefix can give clues
    if api_key.startswith("sk-"):
        print("✓ Key has standard 'sk-' prefix (standard API key)")
    else:
        print(
            "! Key has unusual prefix. This might be a special or organization-specific key."
        )

    # Method 2: Attempt actions that might be limited by key type
    try:
        client = OpenAI(api_key=api_key)

        # Check fine-tuning permissions (often limited)
        try:
            # Just a list call, won't actually create anything
            client.fine_tuning.jobs.list(limit=1)
            print("✓ Key has fine-tuning permissions (suggests a paid account)")
        except OpenAIError as e:
            if "permission" in str(e).lower() or "not authorized" in str(e).lower():
                print(
                    "! Key does not have fine-tuning permissions (suggests a restricted key)"
                )

    except Exception as e:
        print(f"! Could not determine key type: {e}")


def create_diagnostic_report(api_key):
    """Generate a comprehensive diagnostic report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "api_key_prefix": f"{api_key[:4]}..." if api_key else "No API key found",
        "test_results": {},
    }

    # Perform all tests
    try:
        api_info_ok = test_api_info(api_key)
        report["test_results"]["api_info"] = {"success": api_info_ok}

        if api_info_ok:
            # Only continue if the API key is valid
            completion_ok = test_simple_completion(api_key)
            report["test_results"]["simple_completion"] = {"success": completion_ok}

            if completion_ok:
                # Only test rate limits if basic completion works
                rate_limits_ok = test_rate_limits(api_key)
                report["test_results"]["rate_limits"] = {"success": rate_limits_ok}

                # Test model access
                test_model_access(api_key)

                # Check key type
                check_key_type(api_key)
    except Exception as e:
        print(f"Error during testing: {e}")
        report["error"] = str(e)

    # Save report to file
    report_path = Path(r"tests\openai_diagnostic_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nDiagnostic report saved to {report_path.absolute()}")

    # Provide recommendations based on test results
    print("\n=== RECOMMENDATIONS ===")

    if not report["test_results"].get("api_info", {}).get("success", False):
        print("! Your API key appears to be invalid or has been revoked.")
        print("  - Generate a new API key at https://platform.openai.com/api-keys")
        print("  - Update your .env file with the new key")

    elif not report["test_results"].get("simple_completion", {}).get("success", False):
        print("! Your API key is valid but cannot perform completions.")
        print(
            "  - Check if your account has billing issues at https://platform.openai.com/account/billing"
        )
        print(
            "  - Verify your usage limits at https://platform.openai.com/account/limits"
        )
        print("  - Consider creating a new API key")

    elif not report["test_results"].get("rate_limits", {}).get("success", False):
        print("! You appear to be hitting rate limits.")
        print("  - Implement exponential backoff in your application")
        print("  - Reduce the frequency of requests")
        print("  - Consider upgrading your usage tier if available")

    else:
        print("✓ All basic tests passed. If you're still experiencing issues:")
        print("  - Check if you're using a model that your account has access to")
        print("  - Verify that your implementation is using the API key correctly")
        print("  - Monitor your usage at https://platform.openai.com/usage")
        print("  - Note that quota issues might be specific to certain models")


def main():
    """Main function to run diagnostics"""
    parser = argparse.ArgumentParser(description="Diagnose OpenAI API issues")
    parser.add_argument("--key", help="OpenAI API key to test (overrides .env file)")
    args = parser.parse_args()

    print("=== OpenAI API Diagnostics ===")
    print(f"Time: {datetime.now().isoformat()}")

    # Get API key (command line overrides environment)
    api_key = args.key if args.key else get_api_key()

    if not api_key:
        print("Cannot proceed without an API key.")
        return

    create_diagnostic_report(api_key)


if __name__ == "__main__":
    main()
