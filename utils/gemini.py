import logging
import json
import re
from google import genai
from google.genai import types
from google.genai.errors import APIError
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gemini_client() -> genai.Client:
    """
    Initializes and returns the Gemini client using config settings.
    Raises ValueError if API Key is missing or default.
    """
    api_key = config.GEMINI_API_KEY
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE":
        logger.error("GEMINI_API_KEY is not configured in .env file.")
        raise ValueError("Missing Gemini API Key. Please set GEMINI_API_KEY in your .env file.")
    return genai.Client(api_key=api_key)

def _extract_json_string(text: str) -> str:
    """
    Cleans markdown code fences, strips conversational preambles/postambles,
    and returns the isolated JSON string.
    """
    if not text:
        return ""

    cleaned = text.strip().lstrip("\ufeff")

    # 1. Search for markdown code fence anywhere in the response
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, cleaned, flags=re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
        # Verify the candidate starts and ends with JSON structural delimiters
        if (candidate.startswith("{") and candidate.endswith("}")) or (
            candidate.startswith("[") and candidate.endswith("]")
        ):
            return candidate

    # 2. If no valid fence, extract the outermost object { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace : last_brace + 1].strip()

    # 3. Check for outermost array [ ... ]
    first_bracket = cleaned.find("[")
    last_bracket = cleaned.rfind("]")
    if first_bracket != -1 and last_bracket > first_bracket:
        return cleaned[first_bracket : last_bracket + 1].strip()

    # 4. Fallback: Return original stripped string
    return cleaned


def generate_json_response(system_instruction: str, prompt: str) -> dict:
    """
    Sends a request to Gemini using the new google-genai SDK, enforcing a JSON response.
    Returns a Python dictionary parsed from the JSON output.
    """
    try:
        client = get_gemini_client()
        
        # Configure output for structured JSON
        cfg = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.2
        )
        
        logger.info(f"Invoking Gemini model: {config.GEMINI_MODEL}")
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=cfg
        )
        
        raw_text = response.text
        if not raw_text:
            logger.error("Gemini returned an empty or null text response.")
            raise ValueError("Gemini returned an empty response. Please verify your inputs or try again.")
            
        logger.info("Successfully received Gemini response text. Attempting JSON parsing...")
        cleaned_json = _extract_json_string(raw_text)
        parsed_data = json.loads(cleaned_json)
        return parsed_data
        
    except APIError as e:
        logger.error(f"Gemini API Exception occurred: {str(e)}")
        raise RuntimeError(f"Gemini API Error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed. Content was: {raw_text if 'raw_text' in locals() else 'None'}")
        raise ValueError("Failed to parse Gemini response as a structured JSON object. The response may have been truncated or malformed.")
    except Exception as e:
        logger.error(f"Unexpected error in Gemini utility: {str(e)}")
        raise e
