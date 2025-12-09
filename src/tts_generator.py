from gtts import gTTS
from typing import List, Dict
import os
import json
from pathlib import Path
import re


def get_language_code_for_tts(lang_code: str) -> str:
    """
    Converts translation language code to gTTS language code.

    Args:
        lang_code: Translation language code (e.g., 'en', 'tr', 'de')

    Returns:
        gTTS language code
    """
    # gTTS language codes mapping
    lang_map = {
        'en': 'en',
        'tr': 'tr',
        'de': 'de',
        'fr': 'fr',
        'es': 'es',
        'it': 'it',
        'ru': 'ru',
        'ja': 'jp',
        'ko': 'ko',
        'zh': 'zh-cn'
    }
    return lang_map.get(lang_code, 'en')  # Default English


def generate_audio_for_text(text: str, lang_code: str, output_path: str) -> float:
    """
    Converts the given text to an audio file using TTS.

    Args:
        text: Text to convert
        lang_code: Language code (e.g., 'en', 'tr')
        output_path: Output file path (.mp3)

    Returns:
        Duration of the audio file (in seconds)
    """
    if not text or not text.strip():
        # Create empty audio file for empty text
        with open(output_path, 'wb') as f:
            f.write(b'')
        return 0.0

    try:
        tts_lang = get_language_code_for_tts(lang_code)
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        tts.save(output_path)

        # Read actual duration of audio file (using MoviePy)
        try:
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(output_path)
            actual_duration = audio.duration
            audio.close()
            return actual_duration
        except Exception as e:
            print(f"Audio duration could not be read, using estimate: {str(e)}")
            # Fallback: Average speech rate: ~150 words/min = ~2.5 words/sec
            word_count = len(text.split())
            estimated_duration = word_count / 2.5
            return estimated_duration
    except Exception as e:
        print(f"TTS error: {str(e)}")
        # Create empty file in case of error
        with open(output_path, 'wb') as f:
            f.write(b'')
        return 0.0


def generate_audio_for_json(json_file_path: str, progress_callback=None) -> str:
    """
    Generates TTS audio files for all slides in the JSON file.

    Args:
        json_file_path: Path to the JSON file
        progress_callback: Progress callback function (optional)

    Returns:
        Path to the updated JSON file
    """
    # Read JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create folder for audio files
    json_dir = os.path.dirname(os.path.abspath(json_file_path))
    json_basename = os.path.splitext(os.path.basename(json_file_path))[0]
    audio_dir = os.path.join(json_dir, f'{json_basename}_audio')
    os.makedirs(audio_dir, exist_ok=True)

    target_lang = data.get('target_language', 'en')
    slides = data.get('slides', [])
    total_slides = len(slides)

    # Create audio file for each slide
    for idx, slide in enumerate(slides, 1):
        slide_number = slide.get('slide_number', idx)
        translated_text = slide.get('translated_text', '')

        # Remove leading slide number line consisting only of digits
        def strip_leading_slide_number(text: str) -> str:
            lines = text.splitlines()
            # Ex: Remove lines starting with only number/punct like "2", "12", "3.", "4)"
            while lines and re.match(r'^\s*\d+\s*[\.)]?\s*$', lines[0]):
                lines.pop(0)
            return "\n".join(lines).lstrip()

        translated_text = strip_leading_slide_number(translated_text)

        if progress_callback:
            progress_callback(f'TTS: Processing Slide {idx}/{total_slides}...')

        # Audio filename
        audio_filename = f'slide_{slide_number:03d}.mp3'
        audio_path = os.path.join(audio_dir, audio_filename)

        # Create audio file with TTS
        duration = generate_audio_for_text(translated_text, target_lang, audio_path)

        # Update JSON
        slide['audio_file'] = audio_path
        slide['duration'] = round(duration, 2)

        print(f"✓ Audio file created for Slide {slide_number}: {audio_filename} ({duration:.2f}s)")

    # Save updated JSON
    output_json_path = json_file_path.replace('.json', '_with_audio.json')
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if progress_callback:
        progress_callback(f'TTS completed! Audio files created for {total_slides} slides.')

    return output_json_path