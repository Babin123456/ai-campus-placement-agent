"""
Smoke test runner for AI Campus Placement Agent.
Executes pytest unit test suite, and checks Gemini API connectivity if an API key is configured.
"""

import subprocess
import sys

import config


def run_tests():
    print("Running automated unit test suite via pytest...")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests", "-v"], check=False)
    if res.returncode != 0:
        print("Test suite execution failed.")
        return res.returncode

    print("All unit tests passed successfully!")

    api_key = config.GEMINI_API_KEY
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        print("Notice: GEMINI_API_KEY is not configured. Skipping live Gemini API check.")
        return 0

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=config.GEMINI_MODEL, contents="Say hello")
        print("Gemini API connection test succeeded:", response.text)
    except Exception as e:
        print(f"Warning: Gemini API live check could not connect: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
