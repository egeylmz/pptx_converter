from typing import List, Dict
import time
import os
from dotenv import load_dotenv # NEW: Import dotenv

# NEW: Load .env from the same directory as this script
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Priority order: DeepL (best quality) -> deep-translator (free) -> googletrans (fallback)
DEEPL_AVAILABLE = False
DEEP_TRANSLATOR_AVAILABLE = False
GOOGLETRANS_AVAILABLE = False

try:
    import deepl
    DEEPL_AVAILABLE = True
    print("✓ DeepL translator loaded (premium quality)")
except ImportError:
    print("✗ DeepL not installed (pip install deepl)")

try:
    from deep_translator import GoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
    print("✓ deep-translator loaded (Google Translate)")
except ImportError:
    print("✗ deep-translator not installed (pip install deep-translator)")

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
    print("✓ googletrans loaded (fallback)")
except (ImportError, AttributeError) as e:
    # googletrans has compatibility issues with newer httpcore versions
    print(f"✗ googletrans not available (compatibility issue: {type(e).__name__})")


def get_deepl_api_key():
    """Get DeepL API key from environment variables (loaded from .env)."""
    # Simply return the key from the environment
    # load_dotenv() above has already populated os.environ with your .env content
    return os.environ.get('DEEPL_API_KEY')


def translate_texts(slides_data: List[Dict], target_lang: str, progress_callback=None) -> List[Dict]:
    """
    Translates slide texts (including AI narrations) to the target language.

    NOW PROPERLY HANDLES:
    - ai_narration field (primary text to translate)
    - Falls back to 'text' field if ai_narration is missing
    """
    translator = None
    engine_name = None

    # Initialize translator
    if DEEPL_AVAILABLE:
        api_key = get_deepl_api_key()
        if api_key:
            try:
                deepl_lang_map = {
                    'en': 'EN-US', 'tr': 'TR', 'de': 'DE', 'fr': 'FR',
                    'es': 'ES', 'it': 'IT', 'ru': 'RU', 'ja': 'JA',
                    'ko': 'KO', 'zh': 'ZH'
                }
                deepl_target = deepl_lang_map.get(target_lang.lower(), target_lang.upper())
                translator = deepl.Translator(api_key)

                def translate_func(text):
                    result = translator.translate_text(text, target_lang=deepl_target)
                    return result.text

                engine_name = "DeepL (Premium)"
                print(f"✓ Using DeepL translator (target: {deepl_target})")
                if progress_callback:
                    progress_callback(f"Using DeepL translator (Premium Quality)")
            except Exception as e:
                print(f"✗ DeepL initialization failed: {e}")
                translator = None

    if translator is None and DEEP_TRANSLATOR_AVAILABLE:
        try:
            translator_obj = GoogleTranslator(source='auto', target=target_lang)
            translator = translator_obj  # FIX: Set translator so next check passes
            translate_func = lambda text: translator_obj.translate(text)
            engine_name = "Google Translate (Free)"
            print(f"✓ Using deep-translator (Google Translate)")
            if progress_callback:
                progress_callback(f"Using Google Translate (Free)")
        except Exception as e:
            print(f"✗ deep-translator initialization failed: {e}")
            translator = None

    if translator is None and GOOGLETRANS_AVAILABLE:
        try:
            translator_obj = Translator()
            translator = translator_obj  # FIX: Set translator so next check passes
            translate_func = lambda text: translator_obj.translate(text, dest=target_lang).text
            engine_name = "googletrans (Fallback)"
            print(f"✓ Using googletrans (fallback)")
            if progress_callback:
                progress_callback(f"Using googletrans (Fallback)")
        except Exception as e:
            print(f"✗ googletrans initialization failed: {e}")
            translator = None

    if translator is None:
        error_msg = (
            "No translation module available!\n"
            "Please install one of:\n"
            "  • pip install deepl (premium, best quality)\n"
            "  • pip install deep-translator (free, good quality)\n"
            "  • pip install googletrans==3.1.0a0 (fallback)"
        )
        raise Exception(error_msg)

    translated_slides = []
    total_slides = len(slides_data)

    for slide in slides_data:
        try:
            # CRITICAL FIX: Use ai_narration if available, otherwise fall back to text
            text_to_translate = slide.get('ai_narration', '') or slide.get('text', '')

            # Store original text separately
            original_text = slide.get('text', '')

            if text_to_translate.strip():
                # Translate main text with retry
                max_retries = 3
                translated_text = None

                for attempt in range(max_retries):
                    try:
                        status_msg = f'[{engine_name}] Translating: Slide {slide["slide_number"]}/{total_slides}'
                        if attempt > 0:
                            status_msg += f' (retry {attempt}/{max_retries})'

                        print(status_msg)
                        if progress_callback:
                            progress_callback(status_msg)

                        translated_text = translate_func(text_to_translate)

                        success_msg = f'✓ Slide {slide["slide_number"]}/{total_slides} completed'
                        print(success_msg)
                        if progress_callback:
                            progress_callback(success_msg)
                        break

                    except Exception as retry_error:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2
                            error_msg = f"✗ Slide {slide['slide_number']} attempt {attempt + 1} failed. Retrying in {wait_time}s..."
                            print(f"{error_msg} Error: {str(retry_error)}")
                            if progress_callback:
                                progress_callback(error_msg)
                            time.sleep(wait_time)
                        else:
                            print(f"✗✗ Slide {slide['slide_number']} all attempts failed!")
                            raise retry_error

                if translated_text is None or not translated_text.strip():
                    raise Exception("Translation result returned empty or None")

                # Translate individual blocks if they exist
                translated_blocks = []
                if slide.get('text_blocks'):
                    for block_idx, block in enumerate(slide['text_blocks']):
                        if block.strip():
                            block_translated = None
                            for attempt in range(max_retries):
                                try:
                                    block_translated = translate_func(block)
                                    break
                                except Exception as retry_error:
                                    if attempt < max_retries - 1:
                                        time.sleep((attempt + 1) * 1)
                                    else:
                                        print(f"Block {block_idx + 1} translation failed: {str(retry_error)}")
                                        raise retry_error
                            translated_blocks.append(block_translated if block_translated else '')
                        else:
                            translated_blocks.append('')

                translated_slide = slide.copy()
                translated_slide['original_text'] = original_text  # Keep original extracted text
                translated_slide['translated_text'] = translated_text  # Translated AI narration
                translated_slide['translated_blocks'] = translated_blocks
                translated_slides.append(translated_slide)

                print(f"Slide {slide['slide_number']} translated: {translated_text[:50]}...")

                # Rate limiting
                if engine_name == "DeepL (Premium)":
                    time.sleep(0.1)
                else:
                    time.sleep(0.5)

                if progress_callback:
                    progress_callback(f'Slide {slide["slide_number"]}/{total_slides} processed')
            else:
                # Empty slide
                translated_slide = slide.copy()
                translated_slide['original_text'] = original_text
                translated_slide['translated_text'] = ''
                translated_slide['translated_blocks'] = []
                translated_slides.append(translated_slide)

        except Exception as e:
            import traceback
            error_msg = f"Error translating Slide {slide['slide_number']}: {str(e)}"
            print(error_msg)
            print(f"Detailed error: {traceback.format_exc()}")

            if progress_callback:
                progress_callback(f"✗ Error on slide {slide['slide_number']}: {str(e)}")

            translated_slide = slide.copy()
            translated_slide['original_text'] = slide.get('text', '')
            translated_slide['translated_text'] = ''
            translated_slide['translated_blocks'] = []
            translated_slide['translation_error'] = str(e)
            translated_slides.append(translated_slide)

    success_count = sum(1 for s in translated_slides if s.get('translated_text'))
    summary = f"Translation complete: {success_count}/{total_slides} slides translated using {engine_name}"
    print(summary)
    if progress_callback:
        progress_callback(summary)

    return translated_slides


def translate_single_text(text: str, target_lang: str) -> str:
    """Translates a single piece of text."""
    try:
        if DEEPL_AVAILABLE:
            api_key = get_deepl_api_key()
            if api_key:
                translator = deepl.Translator(api_key)
                result = translator.translate_text(text, target_lang=target_lang.upper())
                return result.text

        if DEEP_TRANSLATOR_AVAILABLE:
            translator = GoogleTranslator(source='auto', target=target_lang)
            return translator.translate(text)

        if GOOGLETRANS_AVAILABLE:
            translator = Translator()
            return translator.translate(text, dest=target_lang).text

        raise Exception("No translation module available.")

    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text


def check_translation_services():
    """Check which translation services are available and working"""
    print("\n=== Translation Services Status ===")

    # get_deepl_api_key will now check os.environ (loaded from .env)
    services = {
        "DeepL (Premium)": DEEPL_AVAILABLE and get_deepl_api_key() is not None,
        "deep-translator (Google Free)": DEEP_TRANSLATOR_AVAILABLE,
        "googletrans (Fallback)": GOOGLETRANS_AVAILABLE
    }

    for service, available in services.items():
        status = "✓ Available" if available else "✗ Not available"
        print(f"{service}: {status}")

    if DEEPL_AVAILABLE and not get_deepl_api_key():
        print("\n⚠ DeepL is installed but no API key found!")
        print("Check that DEEPL_API_KEY is present in your .env file.")

    print("=" * 40 + "\n")


check_translation_services()