"""
Complete Setup Testing Suite
Tests all APIs, installations, and configurations

Run this after setup to verify everything is working!
"""

import os
import sys
import platform
from typing import Dict, List, Tuple


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


# ============================================================================
# TEST 1: System Requirements
# ============================================================================

def test_system_requirements() -> bool:
    """Test basic system requirements"""
    print_header("TEST 1: System Requirements")

    all_passed = True

    # Python version
    py_version = sys.version_info
    if py_version >= (3, 8):
        print_success(f"Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    else:
        print_error(f"Python version too old: {py_version.major}.{py_version.minor}")
        print_info("Required: Python 3.8 or higher")
        all_passed = False

    # Operating System
    os_name = platform.system()
    if os_name == "Windows":
        print_success(f"Operating System: {os_name}")
    else:
        print_warning(f"Operating System: {os_name}")
        print_info("This app is designed for Windows (COM interface for PowerPoint)")

    # Check if .env file exists
    if os.path.exists('.env'):
        print_success(".env file found")
    else:
        print_error(".env file NOT found")
        print_info("Copy .env.template to .env and add your API keys")
        all_passed = False

    return all_passed


# ============================================================================
# TEST 2: Required Python Packages
# ============================================================================

def test_python_packages() -> bool:
    """Test if all required packages are installed"""
    print_header("TEST 2: Python Package Installation")

    required_packages = {
        'Core Packages': [
            ('python-pptx', 'pptx'),
            ('flet', 'flet'),
            ('python-dotenv', 'dotenv'),
            ('moviepy', 'moviepy.editor'),
            ('gtts', 'gtts'),
        ],
        'AI & ML': [
            ('google-genai (NEW SDK)', 'google.genai'),
            ('OR google-generativeai (OLD SDK)', 'google.generativeai'),
        ],
        'Windows COM': [
            ('pywin32', 'win32com.client'),
        ]
    }

    optional_packages = {
        'Translation Engines (need at least ONE)': [
            ('deepl', 'deepl'),
            ('deep-translator', 'deep_translator'),
            ('googletrans', 'googletrans'),
        ],
        'Premium TTS': [
            ('google-cloud-texttospeech', 'google.cloud.texttospeech'),
        ]
    }

    all_passed = True

    # Test required packages
    for category, packages in required_packages.items():
        print(f"\n{Colors.BOLD}{category}:{Colors.END}")
        for display_name, import_name in packages:
            try:
                if import_name.startswith('OR '):
                    continue  # Skip OR alternatives
                __import__(import_name)
                print_success(f"{display_name}")
            except ImportError:
                # Check if it's an alternative (google SDK)
                if 'google.genai' in import_name or 'google.generativeai' in import_name:
                    try:
                        if 'genai' in import_name:
                            __import__('google.generativeai')
                            print_success(f"google-generativeai (OLD SDK) - OK")
                        else:
                            __import__('google.genai')
                            print_success(f"google-genai (NEW SDK) - OK")
                    except ImportError:
                        print_error(f"{display_name} - NOT INSTALLED")
                        print_info(f"Install with: pip install {display_name.split()[0]}")
                        all_passed = False
                else:
                    print_error(f"{display_name} - NOT INSTALLED")
                    print_info(f"Install with: pip install {display_name.split()[0]}")
                    all_passed = False

    # Test optional packages
    for category, packages in optional_packages.items():
        print(f"\n{Colors.BOLD}{category}:{Colors.END}")
        at_least_one = False
        for display_name, import_name in packages:
            try:
                __import__(import_name)
                print_success(f"{display_name}")
                at_least_one = True
            except ImportError:
                print_warning(f"{display_name} - not installed (optional)")

        if 'Translation' in category and not at_least_one:
            print_error("No translation engine found!")
            print_info("Install at least one: pip install deep-translator")
            all_passed = False

    return all_passed


# ============================================================================
# TEST 3: Environment Variables & API Keys
# ============================================================================

def test_environment_variables() -> bool:
    """Test if API keys are properly configured"""
    print_header("TEST 3: Environment Variables & API Keys")

    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print_success("Loaded .env file")
    except Exception as e:
        print_error(f"Failed to load .env: {e}")
        return False

    all_passed = True

    # Test GOOGLE_API_KEY (REQUIRED)
    print(f"\n{Colors.BOLD}Required Keys:{Colors.END}")
    google_key = os.environ.get('GOOGLE_API_KEY')
    if google_key:
        masked_key = google_key[:10] + '...' + google_key[-4:]
        print_success(f"GOOGLE_API_KEY found ({masked_key})")
    else:
        print_error("GOOGLE_API_KEY not found!")
        print_info("Add to .env: GOOGLE_API_KEY=your_key_here")
        print_info("Get key from: https://makersuite.google.com/app/apikey")
        all_passed = False

    # Test optional keys
    print(f"\n{Colors.BOLD}Optional Keys (for better quality):{Colors.END}")

    deepl_key = os.environ.get('DEEPL_API_KEY')
    if deepl_key:
        masked_key = deepl_key[:10] + '...' + deepl_key[-4:]
        print_success(f"DEEPL_API_KEY found ({masked_key})")
    else:
        print_warning("DEEPL_API_KEY not found (will use free translation)")
        print_info("Get key from: https://www.deepl.com/pro-api")

    cloud_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if cloud_creds:
        if os.path.exists(cloud_creds):
            print_success(f"GOOGLE_APPLICATION_CREDENTIALS: {cloud_creds}")
        else:
            print_error(f"GOOGLE_APPLICATION_CREDENTIALS path invalid: {cloud_creds}")
            print_info("File does not exist!")
    else:
        print_warning("GOOGLE_APPLICATION_CREDENTIALS not set (will use free gTTS)")
        print_info("Set up Google Cloud TTS for better voice quality")

    return all_passed


# ============================================================================
# TEST 4: Google Gemini API Connection
# ============================================================================

def test_gemini_api() -> bool:
    """Test Gemini API connection and permissions"""
    print_header("TEST 4: Google Gemini API Connection")

    google_key = os.environ.get('GOOGLE_API_KEY')
    if not google_key:
        print_error("GOOGLE_API_KEY not found - skipping API test")
        return False

    # Test NEW SDK first
    try:
        from google import genai
        from google.genai import types

        print_info("Testing NEW Google GenAI SDK (Gemini 2.x)...")
        client = genai.Client(api_key=google_key)

        # Try a simple request
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say 'API test successful' in exactly 3 words.",
            config=types.GenerateContentConfig(temperature=0.1)
        )

        result = response.text.strip()
        print_success("NEW SDK works! Response: " + result[:50])
        print_success("✓ Gemini API is working correctly!")
        print_info("Using: gemini-2.0-flash")
        return True

    except ImportError:
        print_info("NEW SDK not installed, trying OLD SDK...")

        # Try OLD SDK
        try:
            import google.generativeai as old_genai

            print_info("Testing OLD Google GenerativeAI SDK (Gemini 1.5)...")
            old_genai.configure(api_key=google_key)
            model = old_genai.GenerativeModel("gemini-1.5-flash")

            response = model.generate_content("Say 'API test successful' in exactly 3 words.")
            result = response.text.strip()

            print_success("OLD SDK works! Response: " + result[:50])
            print_success("✓ Gemini API is working correctly!")
            print_info("Using: gemini-1.5-flash")
            return True

        except ImportError:
            print_error("Neither NEW nor OLD Gemini SDK is installed!")
            print_info("Install one: pip install google-genai")
            return False

    except Exception as e:
        error_msg = str(e)

        if '403' in error_msg or 'PERMISSION_DENIED' in error_msg:
            print_error("API Key is invalid or lacks permissions!")
            print_info("Check your key at: https://makersuite.google.com/app/apikey")
        elif '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg:
            print_error("Rate limit exceeded!")
            print_info("Wait a moment and try again")
        else:
            print_error(f"API Error: {error_msg}")

        return False


# ============================================================================
# TEST 5: Translation Engines
# ============================================================================

def test_translation_engines() -> bool:
    """Test available translation engines"""
    print_header("TEST 5: Translation Engines")

    engines_working = []

    # Test DeepL
    print(f"\n{Colors.BOLD}Testing DeepL (Premium):{Colors.END}")
    try:
        import deepl
        api_key = os.environ.get('DEEPL_API_KEY')

        if api_key:
            translator = deepl.Translator(api_key)
            result = translator.translate_text("Hello", target_lang="DE")
            print_success(f"DeepL works! Test: 'Hello' → '{result.text}'")
            engines_working.append('DeepL')
        else:
            print_warning("DeepL installed but no API key")
    except ImportError:
        print_info("DeepL not installed")
    except Exception as e:
        print_error(f"DeepL error: {e}")

    # Test deep-translator
    print(f"\n{Colors.BOLD}Testing deep-translator (Free):{Colors.END}")
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='en', target='de')
        result = translator.translate("Hello")
        print_success(f"deep-translator works! Test: 'Hello' → '{result}'")
        engines_working.append('deep-translator')
    except ImportError:
        print_info("deep-translator not installed")
    except Exception as e:
        print_error(f"deep-translator error: {e}")

    # Test googletrans
    print(f"\n{Colors.BOLD}Testing googletrans (Fallback):{Colors.END}")
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate("Hello", dest='de')
        print_success(f"googletrans works! Test: 'Hello' → '{result.text}'")
        engines_working.append('googletrans')
    except ImportError:
        print_info("googletrans not installed")
    except Exception as e:
        print_error(f"googletrans error: {e}")

    # Summary
    print(f"\n{Colors.BOLD}Translation Summary:{Colors.END}")
    if engines_working:
        print_success(f"Working engines: {', '.join(engines_working)}")
        print_info(f"App will use: {engines_working[0]}")
        return True
    else:
        print_error("No translation engines working!")
        print_info("Install at least one: pip install deep-translator")
        return False


# ============================================================================
# TEST 6: TTS Engines
# ============================================================================

def test_tts_engines() -> bool:
    """Test Text-to-Speech engines"""
    print_header("TEST 6: Text-to-Speech Engines")

    engines_working = []

    # Test Google Cloud TTS
    print(f"\n{Colors.BOLD}Testing Google Cloud TTS (Premium):{Colors.END}")
    try:
        from google.cloud import texttospeech

        creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if creds and os.path.exists(creds):
            client = texttospeech.TextToSpeechClient()

            # Try a minimal request (doesn't use quota)
            voices = client.list_voices()
            print_success("Google Cloud TTS works!")
            print_info(f"Available voices: {len(voices.voices)} languages")
            engines_working.append('Cloud TTS')
        else:
            print_warning("Cloud TTS installed but credentials not configured")
            print_info("Set GOOGLE_APPLICATION_CREDENTIALS in .env")

    except ImportError:
        print_info("Cloud TTS not installed")
    except Exception as e:
        print_error(f"Cloud TTS error: {e}")

    # Test gTTS
    print(f"\n{Colors.BOLD}Testing gTTS (Free):{Colors.END}")
    try:
        from gtts import gTTS
        import tempfile

        # Create test audio
        tts = gTTS(text="Test", lang='en')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(temp_file.name)

        # Check file exists
        if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
            print_success("gTTS works!")
            engines_working.append('gTTS')
            os.unlink(temp_file.name)
        else:
            print_error("gTTS created empty file")

    except ImportError:
        print_error("gTTS not installed")
        print_info("Install: pip install gtts")
    except Exception as e:
        print_error(f"gTTS error: {e}")

    # Summary
    print(f"\n{Colors.BOLD}TTS Summary:{Colors.END}")
    if engines_working:
        print_success(f"Working engines: {', '.join(engines_working)}")
        print_info(f"App will use: {engines_working[0]}")
        return True
    else:
        print_error("No TTS engines working!")
        return False


# ============================================================================
# TEST 7: Video Processing
# ============================================================================

def test_video_processing() -> bool:
    """Test MoviePy and FFmpeg"""
    print_header("TEST 7: Video Processing (MoviePy & FFmpeg)")

    try:
        from moviepy.editor import ImageClip, AudioFileClip
        import numpy as np
        import tempfile

        print_info("Testing MoviePy...")

        # Create a simple 1-second test video
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        clip = ImageClip(img, duration=1).set_fps(24)

        # Try to write it
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        clip.write_videofile(temp_file.name, verbose=False, logger=None)

        # Check if file was created
        if os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
            print_success("MoviePy works!")
            print_success("FFmpeg is working correctly!")
            os.unlink(temp_file.name)
            return True
        else:
            print_error("MoviePy created empty file")
            return False

    except ImportError as e:
        print_error(f"MoviePy not installed: {e}")
        print_info("Install: pip install moviepy")
        return False
    except Exception as e:
        error_msg = str(e)

        if 'ffmpeg' in error_msg.lower():
            print_error("FFmpeg not found!")
            print_info("Install FFmpeg:")
            print_info("  Option 1: pip install imageio-ffmpeg")
            print_info("  Option 2: Download from https://ffmpeg.org")
        else:
            print_error(f"Video processing error: {e}")

        return False


# ============================================================================
# TEST 8: PowerPoint Processing (Windows)
# ============================================================================

def test_powerpoint_processing() -> bool:
    """Test PowerPoint processing capabilities"""
    print_header("TEST 8: PowerPoint Processing")

    # Test python-pptx
    print(f"\n{Colors.BOLD}Testing python-pptx:{Colors.END}")
    try:
        from pptx import Presentation
        print_success("python-pptx is working")
    except ImportError:
        print_error("python-pptx not installed")
        print_info("Install: pip install python-pptx")
        return False

    # Test Windows COM (for .ppt conversion)
    if platform.system() == "Windows":
        print(f"\n{Colors.BOLD}Testing Windows COM (for .ppt conversion):{Colors.END}")
        try:
            import win32com.client
            print_success("pywin32 is working")

            # Try to detect PowerPoint
            try:
                powerpoint = win32com.client.Dispatch("PowerPoint.Application")
                powerpoint.Visible = 0
                powerpoint.Quit()
                del powerpoint
                print_success("Microsoft PowerPoint detected")
            except Exception as e:
                print_warning("PowerPoint COM interface not accessible")
                print_info("This is OK if you only use .pptx files")
                print_info(f"Error: {e}")

        except ImportError:
            print_error("pywin32 not installed")
            print_info("Install: pip install pywin32")
            return False
    else:
        print_warning("Not on Windows - .ppt conversion unavailable")

    return True


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests and provide summary"""

    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║          PRESENTATION TO LECTURE - SETUP TEST SUITE                ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

    results = {}

    # Run all tests
    results['System Requirements'] = test_system_requirements()
    results['Python Packages'] = test_python_packages()
    results['Environment Variables'] = test_environment_variables()
    results['Gemini API'] = test_gemini_api()
    results['Translation Engines'] = test_translation_engines()
    results['TTS Engines'] = test_tts_engines()
    results['Video Processing'] = test_video_processing()
    results['PowerPoint Processing'] = test_powerpoint_processing()

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASSED{Colors.END}" if result else f"{Colors.RED}FAILED{Colors.END}"
        print(f"{test_name:.<50} {status}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}\n")

    # Final verdict
    critical_tests = ['System Requirements', 'Python Packages', 'Environment Variables', 'Gemini API']
    critical_passed = all(results.get(test, False) for test in critical_tests)

    if critical_passed and passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║                                                                    ║")
        print("║                   ✓ ALL TESTS PASSED!                              ║")
        print("║                                                                    ║")
        print("║              Your setup is perfect! Ready to run:                  ║")
        print("║                      python main.py                                ║")
        print("║                                                                    ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}")
        return True

    elif critical_passed:
        print(f"{Colors.YELLOW}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║                                                                    ║")
        print("║              ✓ CORE FUNCTIONALITY READY!                           ║")
        print("║                                                                    ║")
        print("║    Some optional features unavailable but app will work.           ║")
        print("║    You can still run: python main.py                               ║")
        print("║                                                                    ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}")

        # List what's missing
        print("\n" + Colors.YELLOW + "Missing optional features:" + Colors.END)
        for test_name, result in results.items():
            if not result and test_name not in critical_tests:
                print(f"  • {test_name}")
        print()
        return True

    else:
        print(f"{Colors.RED}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║                                                                    ║")
        print("║                   ✗ SETUP INCOMPLETE                               ║")
        print("║                                                                    ║")
        print("║         Please fix the failed tests before running.                ║")
        print("║                                                                    ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}")

        # List critical failures
        print("\n" + Colors.RED + "Critical issues to fix:" + Colors.END)
        for test_name in critical_tests:
            if not results.get(test_name, False):
                print(f"  • {test_name}")
        print()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)