"""
Content Enricher Module - FIXED
AI-powered content enrichment for PowerPoint presentations.
"""

import os
import logging
import time
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

# Import enrichment configuration
from enrichment_config import (
    get_enrichment_level_config,
    get_enrichment_prompt,
    format_prompt,
    ENRICHMENT_LEVELS
)

# Try to import Gemini SDK
SDK_VERSION = None
try:
    from google import genai
    from google.genai import types
    SDK_VERSION = "NEW"
    logger.info("✓ Content Enricher: Using NEW Google GenAI SDK")
except ImportError:
    try:
        import google.generativeai as old_genai
        SDK_VERSION = "OLD"
        logger.info("✓ Content Enricher: Using OLD Google GenerativeAI SDK")
    except ImportError:
        logger.error("✗ Content Enricher: No Google Gemini SDK found")
        SDK_VERSION = None


class ContentEnricher:
    """
    AI-powered content enricher for presentation slides.

    Uses Google Gemini to analyze slide content and add relevant
    supplementary information based on the selected enrichment level.
    """

    def __init__(self, enrichment_level: str = "normal"):
        """
        Initialize the ContentEnricher.

        Args:
            enrichment_level: Level of enrichment (none, minimal, normal, detailed, academic)
        """
        if not SDK_VERSION:
            raise ImportError("Google Gemini SDK not installed. pip install google-genai")

        self.enrichment_level = enrichment_level.lower()
        self.level_config = get_enrichment_level_config(self.enrichment_level)
        self.presentation_topic = ""
        self.enrichment_history = []

        # Get API key (already loaded by main.py)
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables!")

        # Initialize Gemini client
        try:
            if SDK_VERSION == "NEW":
                self.client = genai.Client(api_key=api_key)
                self.model_name = "gemini-2.0-flash"
                logger.info(f"✓ Content Enricher initialized with model: {self.model_name}")
            else:
                old_genai.configure(api_key=api_key)
                self.model = old_genai.GenerativeModel("gemini-1.5-flash")
                logger.info("✓ Content Enricher initialized with model: gemini-1.5-flash")
        except Exception as e:
            logger.error(f"✗ Failed to initialize Gemini for enrichment: {e}")
            raise

        logger.info(f"🔬 Enrichment level: {self.level_config['name']}")

    def set_enrichment_level(self, level: str) -> None:
        """
        Change the enrichment level.

        Args:
            level: New enrichment level
        """
        self.enrichment_level = level.lower()
        self.level_config = get_enrichment_level_config(self.enrichment_level)
        logger.info(f"🔬 Enrichment level changed to: {self.level_config['name']}")

    def set_presentation_topic(self, topic: str) -> None:
        """
        Set the overall presentation topic for better context.

        Args:
            topic: Main topic/title of the presentation
        """
        self.presentation_topic = topic
        logger.info(f"📚 Presentation topic set: {topic}")

    def _detect_topic_from_slides(self, slides_data: List[Dict]) -> str:
        """
        Auto-detect the presentation topic from first slide.

        Args:
            slides_data: List of slide dictionaries

        Returns:
            Detected topic string
        """
        if not slides_data:
            return "General presentation"

        first_slide = slides_data[0]
        text = first_slide.get("text", "")

        # Use title or first line as topic
        lines = text.strip().split("\n")
        if lines:
            topic = lines[0].strip()
            if len(topic) > 100:
                topic = topic[:100] + "..."
            return topic

        return "General presentation"

    def _get_previous_context(self) -> str:
        """
        Get context from previously enriched slides.

        Returns:
            Summary of previous content for flow
        """
        if not self.enrichment_history:
            return ""

        # Get last 2 enrichments for context
        recent = self.enrichment_history[-2:]
        context_parts = []

        for item in recent:
            slide_num = item.get("slide_number", "?")
            summary = item.get("summary", "")[:100]
            context_parts.append(f"Slide {slide_num}: {summary}...")

        return "\n".join(context_parts)

    def enrich_slide(self, slide_text: str, slide_number: int = 1,
                     progress_callback=None) -> str:
        """
        Enrich a single slide's content.

        Args:
            slide_text: Original slide text
            slide_number: Slide number for context
            progress_callback: Optional callback for progress updates

        Returns:
            Enriched narration text
        """
        # If enrichment is "none", just return cleaned text
        if self.enrichment_level == "none":
            logger.info(f"📝 Slide {slide_number}: No enrichment (level=none)")
            return slide_text.strip()

        # Skip empty slides
        if not slide_text or len(slide_text.strip()) < 5:
            return slide_text

        if progress_callback:
            progress_callback(f"🔬 Enriching slide {slide_number} ({self.level_config['name']})...")

        # Build the prompt
        previous_context = self._get_previous_context()
        prompt = format_prompt(
            level=self.enrichment_level,
            slide_text=slide_text,
            previous_context=previous_context,
            presentation_topic=self.presentation_topic
        )

        # Get enriched content from Gemini
        enriched_text = self._call_gemini(prompt, slide_number)

        # Store in history for context
        self.enrichment_history.append({
            "slide_number": slide_number,
            "original": slide_text[:100],
            "summary": enriched_text[:100] if enriched_text else slide_text[:100]
        })

        return enriched_text if enriched_text else slide_text

    def _call_gemini(self, prompt: str, slide_number: int) -> Optional[str]:
        """
        Call Gemini API to get enriched content.

        Args:
            prompt: Formatted prompt
            slide_number: For logging

        Returns:
            Enriched text or None on failure
        """
        temperature = self.level_config.get("temperature", 0.7)

        for attempt in range(1, 3):
            try:
                if SDK_VERSION == "NEW":
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=temperature
                        ),
                    )
                    result = response.text
                else:
                    response = self.model.generate_content(prompt)
                    result = response.text

                if result and result.strip():
                    logger.info(f"✓ Slide {slide_number} enriched successfully")
                    return result.strip()
                else:
                    logger.warning(f"⚠ Slide {slide_number}: Empty response from Gemini")

            except Exception as e:
                error_msg = str(e)

                # --- CHANGE START: Critical Error Check ---
                # Check for API Key errors or Bad Requests (400) to stop retrying immediately
                critical_errors = ["400", "403", "API_KEY", "INVALID_ARGUMENT", "PERMISSION_DENIED"]
                if any(err in error_msg for err in critical_errors):
                    logger.error(f"✗ Critical API Error: {error_msg}")
                    return None  # Return immediately, do not retry
                # --- CHANGE END ---

                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    logger.warning(f"⚠ Rate limit hit, waiting...")
                    time.sleep(5)
                else:
                    logger.warning(f"⚠ Attempt {attempt} failed: {e}")

                if attempt == 2:
                    return None

            time.sleep(0.5)

        return None

    def enrich_all_slides(self, slides_data: List[Dict],
                          progress_callback=None) -> List[Dict]:
        """
        Enrich all slides in a presentation.

        Args:
            slides_data: List of slide dictionaries with 'text' field
            progress_callback: Optional callback for progress updates

        Returns:
            Updated slides_data with 'enriched_text' field added
        """
        total = len(slides_data)
        self.enrichment_history = []  # Reset for new presentation

        # Auto-detect topic if not set
        if not self.presentation_topic:
            self.presentation_topic = self._detect_topic_from_slides(slides_data)
            logger.info(f"📚 Auto-detected topic: {self.presentation_topic}")

        logger.info(f"\n{'='*60}")
        logger.info(f"🔬 CONTENT ENRICHMENT STARTED")
        logger.info(f"{'='*60}")
        logger.info(f"Level: {self.level_config['name']}")
        logger.info(f"Slides: {total}")
        logger.info(f"Topic: {self.presentation_topic}")
        logger.info(f"{'='*60}\n")

        for idx, slide in enumerate(slides_data, 1):
            original_text = slide.get("text", "")

            if progress_callback:
                progress_callback(f"🔬 Enriching slide {idx}/{total}...")

            # Enrich the slide
            enriched = self.enrich_slide(
                slide_text=original_text,
                slide_number=idx,
                progress_callback=progress_callback
            )

            # Store enriched text
            slide["enriched_text"] = enriched
            slide["enrichment_level"] = self.enrichment_level

            # Small delay to avoid rate limits
            if self.enrichment_level != "none":
                time.sleep(0.5)

        # Log summary
        enriched_count = sum(1 for s in slides_data if s.get("enriched_text"))
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ ENRICHMENT COMPLETE: {enriched_count}/{total} slides")
        logger.info(f"{'='*60}\n")

        if progress_callback:
            progress_callback(f"✅ Enrichment complete: {enriched_count}/{total} slides")

        return slides_data

    def get_enrichment_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the enrichment process.

        Returns:
            Dictionary with enrichment statistics
        """
        return {
            "level": self.enrichment_level,
            "level_name": self.level_config["name"],
            "slides_processed": len(self.enrichment_history),
            "topic": self.presentation_topic,
            "history": self.enrichment_history
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def enrich_slides_quick(slides_data: List[Dict], level: str = "normal",
                        progress_callback=None) -> List[Dict]:
    """
    Quick function to enrich slides without creating a class instance.

    Args:
        slides_data: List of slide dictionaries
        level: Enrichment level
        progress_callback: Optional progress callback

    Returns:
        Enriched slides data
    """
    enricher = ContentEnricher(enrichment_level=level)
    return enricher.enrich_all_slides(slides_data, progress_callback)


def get_enrichment_preview(slide_text: str, level: str = "normal") -> str:
    """
    Get a quick preview of how enrichment would affect a single slide.

    Args:
        slide_text: Slide text to preview
        level: Enrichment level

    Returns:
        Enriched text preview
    """
    enricher = ContentEnricher(enrichment_level=level)
    return enricher.enrich_slide(slide_text)


# ============================================================================
# FOR TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🔬 CONTENT ENRICHER TEST")
    print("=" * 60)

    # Test slide
    test_slides = [
        {
            "slide_number": 1,
            "text": "Introduction to Machine Learning"
        },
        {
            "slide_number": 2,
            "text": "Machine Learning is a subset of AI that enables computers to learn from data."
        }
    ]

    # Test each level
    for level in ["none", "minimal", "normal", "detailed"]:
        print(f"\n📋 Testing level: {level}")
        print("-" * 40)

        try:
            enricher = ContentEnricher(enrichment_level=level)
            result = enricher.enrich_slide(
                test_slides[1]["text"],
                slide_number=2
            )
            print(f"Original: {test_slides[1]['text'][:50]}...")
            print(f"Enriched: {result[:100]}...")
        except Exception as e:
            print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Test complete!")