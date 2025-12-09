from typing import List, Dict
import time

# Use deep-translator (Python 3.14 compatible)
try:
    from deep_translator import GoogleTranslator

    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False
    # Try googletrans as fallback
    try:
        from googletrans import Translator

        GOOGLETRANS_AVAILABLE = True
    except:
        GOOGLETRANS_AVAILABLE = False


def translate_texts(slides_data: List[Dict], target_lang: str, progress_callback=None) -> List[Dict]:
    """
    Translates slide texts to the target language.

    Args:
        slides_data: List returned from extract_text_from_pptx()
        target_lang: Target language code (e.g., 'en', 'tr', 'de')

    Returns:
        List in the same format containing translated texts. 'translated_text' is added to each dict.
    """
    # Select translation engine
    if DEEP_TRANSLATOR_AVAILABLE:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translate_func = lambda text: translator.translate(text)
    elif GOOGLETRANS_AVAILABLE:
        translator = Translator()
        translate_func = lambda text: translator.translate(text, dest=target_lang).text
    else:
        raise Exception("No translation module found. 'deep-translator' or 'googletrans' must be installed.")

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
                        status_msg = f'Translating: Slide {slide["slide_number"]}/{total_slides} (attempt {attempt + 1}/{max_retries})'
                        print(f"Translating Slide {slide['slide_number']}... (attempt {attempt + 1}/{max_retries})")
                        if progress_callback:
                            progress_callback(status_msg)
                        translated_text = translate_func(slide['text'])
                        print(f"✓ Slide {slide['slide_number']} successfully translated")
                        if progress_callback:
                            progress_callback(f'✓ Slide {slide["slide_number"]}/{total_slides} completed')
                        break  # Exit loop if successful
                    except Exception as retry_error:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # Wait 2, 4, 6 seconds
                            print(
                                f"✗ Slide {slide['slide_number']} translation attempt {attempt + 1}/{max_retries} failed. Waiting {wait_time}s... Error: {str(retry_error)}")
                            time.sleep(wait_time)
                        else:
                            print(f"✗✗ Slide {slide['slide_number']} all translation attempts failed!")
                            raise retry_error  # Raise error if last attempt fails

                if translated_text is None or not translated_text.strip():
                    raise Exception("Translation result returned empty or None")

                # Split translated text into paragraphs (preserve original structure)
                translated_blocks = []
                if slide.get('text_blocks'):
                    for block_idx, block in enumerate(slide['text_blocks']):
                        if block.strip():
                            # Retry for each block as well
                            block_translated = None
                            for attempt in range(max_retries):
                                try:
                                    block_translated = translate_func(block)
                                    break
                                except Exception as retry_error:
                                    if attempt < max_retries - 1:
                                        time.sleep((attempt + 1) * 1)  # Shorter wait for blocks
                                    else:
                                        print(f"Block {block_idx + 1} could not be translated: {str(retry_error)}")
                                        raise retry_error
                            translated_blocks.append(block_translated if block_translated else '')
                        else:
                            translated_blocks.append('')

                translated_slide = slide.copy()
                translated_slide['translated_text'] = translated_text
                translated_slide['translated_blocks'] = translated_blocks
                translated_slides.append(translated_slide)

                print(f"Slide {slide['slide_number']} translated: {translated_text[:50]}...")

                # Short wait for rate limiting
                time.sleep(0.5)  # Increased wait time for rate limiting
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
            # Save with empty translation on error (to indicate translation failed)
            translated_slide = slide.copy()
            translated_slide['translated_text'] = ''  # Translation failed
            translated_slide['translated_blocks'] = []
            translated_slide['translation_error'] = str(e)  # Add error message too
            translated_slides.append(translated_slide)

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
        if DEEP_TRANSLATOR_AVAILABLE:
            translator = GoogleTranslator(source='auto', target=target_lang)
            return translator.translate(text)
        elif GOOGLETRANS_AVAILABLE:
            translator = Translator()
            return translator.translate(text, dest=target_lang).text
        else:
            raise Exception("No translation module found.")
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text