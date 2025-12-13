from typing import List, Dict
import time
import os

# Priority order: DeepL (best quality) -> deep-translator (free) -> googletrans (fallback)
DEEPL_AVAILABLE = False
DEEP_TRANSLATOR_AVAILABLE = False
GOOGLETRANS_AVAILABLE = False

# Try DeepL first (premium quality)
try:
    import deepl

    DEEPL_AVAILABLE = True
    print("✓ DeepL translator loaded (premium quality)")
except ImportError:
    print("✗ DeepL not installed (pip install deepl)")

# Try deep-translator (Google Translate wrapper)
try:
    from deep_translator import GoogleTranslator

    DEEP_TRANSLATOR_AVAILABLE = True
    print("✓ deep-translator loaded (Google Translate)")
except ImportError:
    print("✗ deep-translator not installed (pip install deep-translator)")

# Try googletrans as last resort
try:
    from googletrans import Translator

    GOOGLETRANS_AVAILABLE = True
    print("✓ googletrans loaded (fallback)")
except ImportError:
    print("✗ googletrans not installed")


def get_deepl_api_key():
    """
    Get DeepL API key from environment variable or config file.
    You can set it in multiple ways:

    1. Environment variable:
       SET DEEPL_API_KEY=your-key-here  (Windows)
       export DEEPL_API_KEY=your-key-here  (Linux/Mac)

    2. Create a file named 'deepl_config.txt' in the same directory with just your API key

    3. Hardcode it here (not recommended for security):
       return "your-key-here"
    """
    # Method 1: Environment variable
    api_key = os.environ.get('DEEPL_API_KEY')
    if api_key:
        return api_key

    # Method 2: Config file
    config_file = os.path.join(os.path.dirname(__file__), 'deepl_config.txt')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            api_key = f.read().strip()
            if api_key:
                return api_key

    # Method 3: Hardcoded (uncomment and add your key)
    # return "your-api-key-here"

    return None


def translate_texts(slides_data: List[Dict], target_lang: str, progress_callback=None) -> List[Dict]:
    """
    Translates slide texts to the target language using available translation service.
    Priority: DeepL > deep-translator > googletrans

    Args:
        slides_data: List returned from extract_text_from_pptx()
        target_lang: Target language code (e.g., 'en', 'tr', 'de')
        progress_callback: Optional callback function for progress updates

    Returns:
        List in the same format containing translated texts. 'translated_text' is added to each dict.
    """

    # Select translation engine
    translator = None
    engine_name = None

    if DEEPL_AVAILABLE:
        api_key = get_deepl_api_key()
        if api_key:
            try:
                # DeepL uses different language codes for some languages
                # Map common codes to DeepL format
                deepl_lang_map = {
                    'en': 'EN-US',  # or 'EN-GB'
                    'tr': 'TR',
                    'de': 'DE',
                    'fr': 'FR',
                    'es': 'ES',
                    'it': 'IT',
                    'ru': 'RU',
                    'ja': 'JA',
                    'ko': 'KO',
                    'zh': 'ZH'  # Chinese
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
            if slide['text'].strip():
                # Translate text (with retry mechanism)
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

                        translated_text = translate_func(slide['text'])

                        success_msg = f'✓ Slide {slide["slide_number"]}/{total_slides} completed'
                        print(success_msg)
                        if progress_callback:
                            progress_callback(success_msg)
                        break  # Exit loop if successful

                    except Exception as retry_error:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # Wait 2, 4, 6 seconds
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

                # Translate individual blocks (preserves formatting)
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
                translated_slide['translated_text'] = translated_text
                translated_slide['translated_blocks'] = translated_blocks
                translated_slides.append(translated_slide)

                print(f"Slide {slide['slide_number']} translated: {translated_text[:50]}...")

                # Rate limiting (DeepL is more generous, but still be polite)
                if engine_name == "DeepL (Premium)":
                    time.sleep(0.1)  # DeepL can handle higher rates
                else:
                    time.sleep(0.5)  # Be more conservative with free services

                if progress_callback:
                    progress_callback(f'Slide {slide["slide_number"]}/{total_slides} processed')
            else:
                # Empty slide
                translated_slide = slide.copy()
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

            # Save with empty translation on error
            translated_slide = slide.copy()
            translated_slide['translated_text'] = ''
            translated_slide['translated_blocks'] = []
            translated_slide['translation_error'] = str(e)
            translated_slides.append(translated_slide)

    # Final summary
    success_count = sum(1 for s in translated_slides if s.get('translated_text'))
    summary = f"Translation complete: {success_count}/{total_slides} slides translated using {engine_name}"
    print(summary)
    if progress_callback:
        progress_callback(summary)

    return translated_slides


def translate_single_text(text: str, target_lang: str) -> str:
    """
    Translates a single piece of text.

    Args:
        text: Text to translate
        target_lang: Target language code

    Returns:
        Translated text
    """
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


# Test function to check which services are available
def check_translation_services():
    """Check which translation services are available and working"""
    print("\n=== Translation Services Status ===")

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
        print("Set your API key using one of these methods:")
        print("  1. Environment: SET DEEPL_API_KEY=your-key")
        print("  2. File: Create 'deepl_config.txt' with your key")
        print("  3. Edit get_deepl_api_key() function")

    print("=" * 40 + "\n")


# Run check on import
check_translation_services()