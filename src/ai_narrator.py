"""
AI Narrator - Universal Version
Supports BOTH:
- google-genai (NEW, Gemini 2.x)
- google-generativeai (OLD, Gemini 1.5)
"""

import os
import logging
import time
from typing import Optional, List, Dict

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# 🔑 API KEY
# ------------------------------------------------------------
HARDCODED_KEY = "AIzaSyAUuKaS2f4t5QYyo1XnJmkc5noYnzjCtgI"

# ------------------------------------------------------------
# SDK Detection
# ------------------------------------------------------------
SDK_VERSION = None

try:
    from google import genai
    from google.genai import types
    SDK_VERSION = "NEW"
    logger.info("✓ Detected NEW Google GenAI SDK (Gemini 2.x)")
except ImportError:
    try:
        import google.generativeai as old_genai
        SDK_VERSION = "OLD"
        logger.info("✓ Detected OLD Google GenerativeAI SDK (Gemini 1.5)")
    except ImportError:
        logger.error("✗ No Google Gemini SDK found")
        SDK_VERSION = None


def get_gemini_api_key() -> Optional[str]:
    if HARDCODED_KEY and "PASTE_YOUR" not in HARDCODED_KEY:
        return HARDCODED_KEY.strip()
    return os.environ.get("GOOGLE_API_KEY")


class AITeacherNarrator:
    """Converts slide text into natural spoken narration using Gemini."""

    def __init__(self, temperature: float = 0.7, style: str = "engaging"):
        if not SDK_VERSION:
            raise ImportError("Google Gemini SDK not installed.")

        api_key = get_gemini_api_key()
        if not api_key:
            raise ValueError("No API key found.")

        self.temperature = temperature
        self.style = style

        if SDK_VERSION == "NEW":
            self.client = genai.Client(api_key=api_key)
            self.model_name = "gemini-2.0-flash"
        else:
            old_genai.configure(api_key=api_key)
            self.model = old_genai.GenerativeModel("gemini-1.5-flash")

    # ------------------------------------------------------------
    # Prompt Builder
    # ------------------------------------------------------------
    def _build_prompt(self, slide_text: str, slide_number: int, is_title: bool) -> str:
        style_map = {
            "engaging": "conversational and engaging, like a favorite teacher",
            "formal": "formal and academic, suitable for a university lecture",
            "casual": "relaxed and friendly, using simple analogies",
            "enthusiastic": "highly energetic and passionate"
        }
        style_desc = style_map.get(self.style, style_map["engaging"])

        if is_title:
            return (
                "You are a presenter.\n"
                f"Title slide text:\n{slide_text}\n\n"
                f"Create a single-sentence warm introduction.\n"
                f"Style: {style_desc}."
            )

        return (
            "You are an experienced teacher.\n"
            f"Slide text:\n{slide_text}\n\n"
            "Convert this into a natural spoken narration.\n"
            "- Max 3 sentences\n"
            "- Do NOT mention slides or bullet points\n"
            f"Style: {style_desc}."
        )

    # ------------------------------------------------------------
    # Main Narration
    # ------------------------------------------------------------
    def narrate_slides(self, slides_data: List[Dict], progress_callback=None) -> List[Dict]:
        total = len(slides_data)

        for i, slide in enumerate(slides_data, 1):
            text = slide.get("text", "").strip()

            if len(text) < 5:
                slide["ai_narration"] = text
                continue

            if progress_callback:
                progress_callback(f"🤖 Generating narration {i}/{total}")

            is_title = (i == 1) or (len(text.split()) < 15)
            prompt = self._build_prompt(text, i, is_title)

            for attempt in (1, 2):  # retry once
                try:
                    if SDK_VERSION == "NEW":
                        response = self.client.models.generate_content(
                            model=self.model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=self.temperature
                            ),
                        )
                        narration = response.text
                    else:
                        response = self.model.generate_content(prompt)
                        narration = response.text

                    if narration:
                        slide["ai_narration"] = narration.strip()
                        break

                except Exception as e:
                    logger.warning(
                        f"Slide {i} attempt {attempt} failed: {e}"
                    )
                    if attempt == 2:
                        slide["ai_narration"] = text

                time.sleep(0.6)  # safe but faster

        return slides_data


if __name__ == "__main__":
    print(f"SDK detected: {SDK_VERSION}")
