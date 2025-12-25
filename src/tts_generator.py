from gtts import gTTS
from typing import List, Dict
import os
import json
from pathlib import Path
import re

# Google Cloud TTS is optional - fallback to gTTS if not available
CLOUD_TTS_AVAILABLE = False
try:
    from google.cloud import texttospeech
    CLOUD_TTS_AVAILABLE = True
    print("✓ Google Cloud TTS available")
except ImportError:
    print("⚠ Google Cloud TTS not installed, using gTTS only")
    texttospeech = None


def get_language_code_for_tts(lang_code: str) -> str:
    """
    Converts translation language code to gTTS language code.

    CRITICAL FIX: Properly handles Chinese variants

    Args:
        lang_code: Translation language code (e.g., 'en', 'tr', 'zh-CN')

    Returns:
        gTTS language code
    """
    # Direct mapping for exact matches (including Chinese variants)
    lang_map = {
        'en': 'en',
        'tr': 'tr',
        'de': 'de',
        'fr': 'fr',
        'es': 'es',
        'it': 'it',
        'ru': 'ru',
        'ja': 'ja',  # FIXED: was 'jp'
        'ko': 'ko',
        'zh': 'zh-CN',  # Default Chinese
        'zh-CN': 'zh-CN',  # Simplified Chinese
        'zh-TW': 'zh-TW',  # Traditional Chinese
        'pt': 'pt',  # Portuguese
        'nl': 'nl',  # Dutch
        'pl': 'pl',  # Polish
        'ar': 'ar',  # Arabic
        'hi': 'hi',  # Hindi
    }

    result = lang_map.get(lang_code.lower(), 'en')
    print(f"🗣️  TTS Language mapping: {lang_code} → {result}")
    return result


def generate_cloud_tts_audio(
    text: str,
    lang_code: str,
    output_path: str,
    speaking_rate: float = 1.0
) -> float:
    """
    Generate audio using Google Cloud Text-to-Speech.

    Returns:
        Duration in seconds
    """
    if not CLOUD_TTS_AVAILABLE or texttospeech is None:
        raise ImportError("Google Cloud TTS not available")
    
    client = texttospeech.TextToSpeechClient()

    tts_lang = get_language_code_for_tts(lang_code)

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=tts_lang,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    with open(output_path, "wb") as out:
        out.write(response.audio_content)

    # Read duration
    try:
        from moviepy.editor import AudioFileClip
        audio = AudioFileClip(output_path)
        duration = audio.duration
        audio.close()
        return duration
    except Exception:
        # fallback estimation
        word_count = len(text.split())
        return max(word_count / 2.3, 2.0)

def generate_audio_for_text(
    text: str,
    lang_code: str,
    output_path: str,
    speaking_rate: float = 1.0
) -> float:
    """
    Converts text to audio using:
    1. Google Cloud TTS (primary)
    2. gTTS (fallback)
    """

    if not text or not text.strip():
        with open(output_path, 'wb') as f:
            f.write(b'')
        return 2.0

    # --- PRIMARY: Google Cloud TTS ---
    try:
        print("Using Google Cloud TTS")
        return generate_cloud_tts_audio(
            text=text,
            lang_code=lang_code,
            output_path=output_path,
            speaking_rate=speaking_rate
        )
    except Exception as cloud_error:
        print(f"⚠️  Cloud TTS failed: {cloud_error}")
        print("🔁 Falling back to gTTS...")

    # --- FALLBACK: gTTS (existing logic) ---
    try:
        tts_lang = get_language_code_for_tts(lang_code)

        try:
            tts = gTTS(text=text, lang=tts_lang, slow=False, lang_check=True)
        except ValueError:
            print(f"⚠️  gTTS language '{tts_lang}' not supported, falling back to English")
            tts = gTTS(text=text, lang='en', slow=False)

        tts.save(output_path)

        from moviepy.editor import AudioFileClip
        audio = AudioFileClip(output_path)
        duration = audio.duration
        audio.close()
        return duration

    except Exception as e:
        print(f"❌ TTS failed completely: {e}")
        with open(output_path, 'wb') as f:
            f.write(b'')
        return 3.0


def generate_audio_for_json(json_file_path: str, progress_callback=None) -> str:
    """
    Generates TTS audio files for all slides in the JSON file.

    IMPROVED: Better validation and error recovery

    Args:
        json_file_path: Path to the JSON file
        progress_callback: Progress callback function (optional)

    Returns:
        Path to the updated JSON file
    """
    # Read and validate JSON
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON file: {str(e)}")

    # Validate required fields
    if 'slides' not in data:
        raise Exception("JSON missing 'slides' field")

    # Create folder for audio files
    json_dir = os.path.dirname(os.path.abspath(json_file_path))
    json_basename = os.path.splitext(os.path.basename(json_file_path))[0]
    audio_dir = os.path.join(json_dir, f'{json_basename}_audio')
    os.makedirs(audio_dir, exist_ok=True)

    target_lang = data.get('target_language', 'en')
    slides = data.get('slides', [])
    total_slides = len(slides)

    print(f"\n{'=' * 60}")
    print(f"🎙️  TTS GENERATION STARTED")
    print(f"{'=' * 60}")
    print(f"Target Language: {target_lang}")
    print(f"Total Slides: {total_slides}")
    print(f"{'=' * 60}\n")

    success_count = 0
    error_count = 0

    # Create audio file for each slide
    for idx, slide in enumerate(slides, 1):
        slide_number = slide.get('slide_number', idx)

        # CRITICAL: Use translated_text (AI narration in target language)
        translated_text = slide.get('translated_text', '')

        # Fallback chain if translated_text is empty
        if not translated_text:
            translated_text = slide.get('ai_narration', '')
        if not translated_text:
            translated_text = slide.get('text', '')
        if not translated_text:
            translated_text = f"Slide {slide_number}"

        # Debug info
        if idx <= 3:  # Only log first 3 for brevity
            original_preview = slide.get('original_text', '')[:50]
            ai_preview = slide.get('ai_narration', '')[:50]
            translated_preview = translated_text[:50] if translated_text else '(empty)'

            print(f"\n--- Slide {slide_number} ---")
            print(f"Original: {original_preview}...")
            print(f"AI narration: {ai_preview}...")
            print(f"Translated: {translated_preview}...")

        if progress_callback:
            progress_callback(f'TTS: Processing Slide {idx}/{total_slides}...')

        # Clean up text - remove leading slide numbers
        def strip_leading_slide_number(text: str) -> str:
            lines = text.splitlines()
            while lines and re.match(r'^\s*\d+\s*[\.)]?\s*$', lines[0]):
                lines.pop(0)
            return "\n".join(lines).lstrip()

        cleaned_text = strip_leading_slide_number(translated_text)

        # Audio filename
        audio_filename = f'slide_{slide_number:03d}.mp3'
        audio_path = os.path.join(audio_dir, audio_filename)

        # Create audio file with TTS
        try:
            duration = generate_audio_for_text(cleaned_text, target_lang, audio_path, speaking_rate=1.05)

            # Verify file was created
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"✅ Slide {slide_number}: {audio_filename} ({duration:.2f}s)")
                success_count += 1
            else:
                print(f"⚠️  Slide {slide_number}: Audio file empty, using default duration")
                duration = 3.0
                error_count += 1
        except Exception as e:
            print(f"❌ Slide {slide_number}: TTS failed - {str(e)}")
            duration = 3.0
            error_count += 1
            # Create empty file to prevent downstream errors
            with open(audio_path, 'wb') as f:
                f.write(b'')

        # Update JSON with audio info
        slide['audio_file'] = audio_path
        slide['duration'] = round(duration, 2)

    # Save updated JSON
    output_json_path = json_file_path.replace('.json', '_with_audio.json')
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 60}")
    print(f"✅ TTS GENERATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Success: {success_count}/{total_slides} slides")
    if error_count > 0:
        print(f"⚠️  Errors: {error_count} slides (using default duration)")
    print(f"Output: {os.path.basename(output_json_path)}")
    print(f"{'=' * 60}\n")

    if progress_callback:
        if error_count == 0:
            progress_callback(f'✅ TTS completed! {success_count}/{total_slides} slides processed')
        else:
            progress_callback(f'⚠️  TTS completed with {error_count} errors. {success_count}/{total_slides} succeeded')

    return output_json_path
