"""
Gemini Connection Test / Debug Script
Works with BOTH:
- google-genai (NEW)
- google-generativeai (OLD)

Purpose:
- Verify API key
- Verify SDK detection
- Verify text generation
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================
# 🔑 API KEY (same logic as main)
# ===============================
HARDCODED_KEY = "AIzaSyAUuKaS2f4t5QYyo1XnJmkc5noYnzjCtgI"

def get_api_key():
    if HARDCODED_KEY and "PASTE_YOUR" not in HARDCODED_KEY:
        return HARDCODED_KEY.strip()
    return os.environ.get("GOOGLE_API_KEY")


# ===============================
# SDK DETECTION
# ===============================
SDK_VERSION = None

try:
    from google import genai
    from google.genai import types
    SDK_VERSION = "NEW"
    logger.info("✓ NEW google-genai SDK detected")
except ImportError:
    try:
        import google.generativeai as old_genai
        SDK_VERSION = "OLD"
        logger.info("✓ OLD google-generativeai SDK detected")
    except ImportError:
        logger.error("✗ No Gemini SDK installed")
        raise SystemExit(1)


# ===============================
# TEST GENERATION
# ===============================
def run_test():
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError("No API key found")

    prompt = "Say hello in one short sentence."

    try:
        if SDK_VERSION == "NEW":
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.3),
            )
            print("\n--- GEMINI RESPONSE (NEW SDK) ---")
            print(response.text)

        else:
            old_genai.configure(api_key=api_key)
            model = old_genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            print("\n--- GEMINI RESPONSE (OLD SDK) ---")
            print(response.text)

        print("\n✅ Gemini connection OK")

    except Exception as e:
        print("\n❌ Gemini test FAILED")
        print(type(e).__name__, ":", e)


if __name__ == "__main__":
    print(f"\nSDK VERSION: {SDK_VERSION}")
    run_test()
