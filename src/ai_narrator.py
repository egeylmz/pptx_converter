"""
AI Narrator - Enhanced Version with Context Memory
Now remembers previous slides for coherent narration!
"""

import os
import logging
import time
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

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
    """Get Gemini API key from environment variables (already loaded by main.py)."""
    api_key = os.environ.get("GOOGLE_API_KEY")

    if api_key:
        logger.info("✓ API key loaded successfully")
        return api_key.strip()

    logger.error("✗ No API key found! Check your .env file.")
    return None


# Narration style presets
NARRATION_STYLES = {
    "professional": {
        "name": "Professional Lecturer",
        "description": "Formal, academic tone suitable for business and educational presentations",
        "temperature": 0.5,
        "prompt_style": "formal and professional, like a university professor or corporate trainer"
    },
    "engaging": {
        "name": "Engaging Teacher",
        "description": "Conversational and friendly, like your favorite teacher explaining concepts",
        "temperature": 0.7,
        "prompt_style": "conversational and engaging, like a favorite teacher who makes learning fun"
    },
    "enthusiastic": {
        "name": "Enthusiastic Presenter",
        "description": "Energetic and passionate, great for motivational or sales presentations",
        "temperature": 0.8,
        "prompt_style": "highly energetic and passionate, using vivid language and excitement"
    },
    "casual": {
        "name": "Casual Explainer",
        "description": "Relaxed and friendly, using simple language and everyday analogies",
        "temperature": 0.7,
        "prompt_style": "relaxed and friendly, using simple everyday language and relatable examples"
    },
    "storyteller": {
        "name": "Story Teller",
        "description": "Narrative style that weaves information into a compelling story",
        "temperature": 0.8,
        "prompt_style": "narrative and story-driven, connecting ideas into a flowing story"
    }
}


class AITeacherNarrator:
    """
    Enhanced AI Narrator with context awareness and content enrichment.
    Remembers previous slides to create coherent, flowing narration.
    Now supports content enrichment with configurable levels.
    """

    def __init__(self, temperature: float = 0.7, style: str = "engaging", 
                 enrichment_level: str = "none"):
        """
        Initialize the AI Narrator.
        
        Args:
            temperature: AI creativity level (0.0-1.0)
            style: Narration style (professional, engaging, etc.)
            enrichment_level: Content enrichment level (none, minimal, normal, detailed, academic)
        """
        if not SDK_VERSION:
            raise ImportError("Google Gemini SDK not installed.")

        api_key = get_gemini_api_key()
        if not api_key:
            raise ValueError("No API key found!")

        self.temperature = temperature
        self.style = style
        self.enrichment_level = enrichment_level
        self.conversation_history = []
        self.content_enricher = None

        # Initialize Content Enricher if level is not "none"
        if enrichment_level and enrichment_level.lower() != "none":
            try:
                from content_enricher import ContentEnricher
                self.content_enricher = ContentEnricher(enrichment_level=enrichment_level)
                logger.info(f"🔬 Content Enricher initialized: {enrichment_level}")
            except ImportError as e:
                logger.warning(f"⚠ Content Enricher not available: {e}")
                self.content_enricher = None
            except Exception as e:
                logger.warning(f"⚠ Content Enricher initialization failed: {e}")
                self.content_enricher = None

        # Initialize SDK
        try:
            if SDK_VERSION == "NEW":
                self.client = genai.Client(api_key=api_key)
                self.model_name = "gemini-2.0-flash"
                logger.info(f"✓ Using model: {self.model_name}")
            else:
                old_genai.configure(api_key=api_key)
                self.model = old_genai.GenerativeModel("gemini-1.5-flash")
                logger.info("✓ Using model: gemini-1.5-flash")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Gemini: {e}")
            raise

    def _get_style_config(self, style_key: str) -> dict:
        """Get style configuration, with fallback to engaging."""
        return NARRATION_STYLES.get(style_key, NARRATION_STYLES["engaging"])

    def _build_context_aware_prompt(self, slide_text: str, slide_number: int,
                                     total_slides: int, is_title: bool) -> str:
        """
        Build prompt with strict context roles: Opener, Body, or Closer.
        """
        style_config = self._get_style_config(self.style)
        style_desc = style_config["prompt_style"]

        # --- 1. THE OPENER (First Slide) ---
        if slide_number == 1:
            return (
                f"You are the presenter starting a {total_slides}-slide presentation.\n"
                f"This is the Title Slide: '{slide_text}'\n\n"
                "INSTRUCTIONS:\n"
                "1. Start with 'Good morning everyone' (or a similar warm welcome).\n"
                "2. Introduce the topic clearly.\n"
                "3. Give a brief 1-sentence hook about what we will cover.\n"
                f"Tone: {style_desc}"
            )

        # --- 2. THE CLOSER (Last Slide) ---
        elif slide_number == total_slides:
            # Get previous context to bridge the gap
            context = ""
            if self.conversation_history:
                last_slide = self.conversation_history[-1]
                context = f"Previous slide discussed: {last_slide['narration'][:100]}..."

            return (
                f"You are concluding a presentation. This is the Final Slide.\n"
                f"Context from previous slide: {context}\n"
                f"Final Slide Content: {slide_text}\n\n"
                "INSTRUCTIONS:\n"
                "1. Briefly summarize the main takeaway.\n"
                "2. Do NOT say 'Good morning' or introduce yourself.\n"
                "3. End with this exact sign-off: 'Thank you for your attention, and I will see you next week.'\n"
                f"Tone: {style_desc}"
            )

        # --- 3. THE BODY (Middle Slides) ---
        else:
            # Build context from previous slides
            context = ""
            if self.conversation_history:
                # Get last 2 slides for context
                recent_context = self.conversation_history[-2:]
                context_items = []
                for prev_slide in recent_context:
                    prev_num = prev_slide['slide_number']
                    # Take the last sentence of the previous narration to ensure flow
                    prev_narration = prev_slide['narration'][-150:]
                    context_items.append(f"Slide {prev_num} ended with: ...{prev_narration}")
                context = "\n".join(context_items)

            return (
                f"You are narrating slide {slide_number} of {total_slides} (Middle of presentation).\n\n"
                f"PREVIOUS CONTEXT (flow from this):\n{context}\n\n"
                f"CURRENT SLIDE CONTENT:\n{slide_text}\n\n"
                "STRICT INSTRUCTIONS:\n"
                "1. Do NOT say 'Good morning', 'Hello', or 'Welcome' again.\n"
                "2. Do NOT introduce yourself.\n"
                "3. Use a transition phrase (e.g., 'Moving on...', 'Furthermore...', 'As we can see here...') to connect to the previous context.\n"
                "4. Explain the current slide content naturally.\n"
                f"Tone: {style_desc}"
            )

    def narrate_slides(self, slides_data: List[Dict], progress_callback=None) -> List[Dict]:
        """
        Generate context-aware narration for all slides.
        """
        total = len(slides_data)
        self.conversation_history = []

        # New flag to stop processing if API is dead
        api_disabled = False

        logger.info(f"🎭 Using narration style: {self._get_style_config(self.style)['name']}")

        if self.content_enricher:
            logger.info(f"🔬 Content enrichment enabled: {self.enrichment_level}")

        for i, slide in enumerate(slides_data, 1):
            text = slide.get("text", "").strip()

            if len(text) < 5:
                slide["ai_narration"] = text
                continue

            # CRITICAL FIX: Circuit breaker check
            if api_disabled:
                slide["ai_narration"] = text
                continue

            # Step 1: Apply content enrichment
            enriched_text = text
            if self.content_enricher and self.enrichment_level != "none":
                # ... existing enrichment call ...
                try:
                    enriched_text = self.content_enricher.enrich_slide(
                        slide_text=text, slide_number=i, progress_callback=progress_callback
                    )
                    slide["enriched_text"] = enriched_text
                    slide["enrichment_level"] = self.enrichment_level
                except Exception as e:
                    logger.warning(f"⚠ Enrichment failed: {e}")
                    enriched_text = text

            # Step 2: Generate Narration
            # ... Prompt building code remains the same ...
            is_title = (i == 1) or (len(text.split()) < 15)
            prompt = self._build_context_aware_prompt(enriched_text, i, total, is_title)

            for attempt in (1, 2):
                try:
                    # ... API Call logic (NEW/OLD SDK) remains the same ...
                    if SDK_VERSION == "NEW":
                        response = self.client.models.generate_content(
                            model=self.model_name, contents=prompt,
                            config=types.GenerateContentConfig(temperature=self.temperature),
                        )
                        narration = response.text
                    else:
                        response = self.model.generate_content(prompt)
                        narration = response.text

                    if narration and narration.strip():
                        narration = narration.strip()
                        slide["ai_narration"] = narration
                        self.conversation_history.append({
                            'slide_number': i, 'text': text, 'narration': narration
                        })
                        logger.info(f"✓ Slide {i}/{total} narration generated")
                        break
                    else:
                        if attempt == 2: slide["ai_narration"] = enriched_text

                except Exception as e:
                    error_msg = str(e)

                    # CRITICAL FIX: Updated Error Handling
                    critical_errors = ["403", "400", "PERMISSION_DENIED", "API_KEY_INVALID", "API key expired",
                                       "INVALID_ARGUMENT"]
                    if any(x in error_msg for x in critical_errors):
                        logger.error(f"✗ Critical API Error: {error_msg}")
                        slide["ai_narration"] = enriched_text
                        api_disabled = True  # Stop all future API calls
                        break

                    elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        logger.warning(f"⚠ Rate limit hit, waiting...")
                        time.sleep(5)
                        if attempt == 2: slide["ai_narration"] = enriched_text
                    else:
                        logger.warning(f"⚠ Slide {i} failed: {e}")
                        if attempt == 2: slide["ai_narration"] = enriched_text

                time.sleep(0.8)

        return slides_data


def get_available_styles() -> Dict[str, dict]:
    """
    Get all available narration styles for UI display.
    """
    return NARRATION_STYLES


if __name__ == "__main__":
    print(f"SDK detected: {SDK_VERSION}")
    print("\nAvailable Narration Styles:")
    for key, config in NARRATION_STYLES.items():
        print(f"  • {config['name']}: {config['description']}")