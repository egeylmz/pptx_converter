"""
Translation Service Health Checker
Tests if deep-translator, GoogleTranslator, and DeepL are working properly
"""

import sys
import os
from datetime import datetime


# -----------------------------
# Helper Functions
# -----------------------------
def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(service, status, message, details=None):
    icon = "✓" if status == "OK" else "✗"
    color_start = "\033[92m" if status == "OK" else "\033[91m"
    color_end = "\033[0m"

    print(f"\n{color_start}{icon} {service}: {status}{color_end}")
    print(f"   {message}")
    if details:
        print(f"   Details: {details}")


# -----------------------------------------------------------------------------
# TEST: deep-translator Import
# -----------------------------------------------------------------------------
def test_import_deep_translator():
    print_header("TEST 1A: deep-translator Import Check")

    try:
        from deep_translator import GoogleTranslator
        print_result("deep-translator Import", "OK", "Module imported successfully")
        return True, GoogleTranslator
    except Exception as e:
        print_result("deep-translator Import", "FAIL", "Import failed", str(e))
        return False, None


# -----------------------------------------------------------------------------
# TEST: DeepL Import
# -----------------------------------------------------------------------------
def test_import_deepl():
    print_header("TEST 1B: DeepL Import Check")

    try:
        import deepl
        print_result("DeepL Import", "OK", "DeepL module imported successfully")
        return True, deepl
    except Exception as e:
        print_result("DeepL Import", "FAIL", "DeepL package not installed", str(e))
        print("   Install with: pip install deepl")
        return False, None


# -----------------------------------------------------------------------------
# TEST: DeepL API Key
# -----------------------------------------------------------------------------
def test_deepl_api_key():
    print_header("TEST 1C: DeepL API Key Check")

    api_key = (
        os.environ.get("DEEPL_API_KEY")
        or (open("../deepl_config.txt").read().strip() if os.path.exists("../deepl_config.txt") else None)
    )

    if api_key:
        print_result("DeepL API Key", "OK", "API Key found")
        return True, api_key
    else:
        print_result("DeepL API Key", "FAIL", "No API Key found")
        print("   Set environment variable: DEEPL_API_KEY=your-key")
        print("   Or create deepl_config.txt with your key")
        return False, None


# -----------------------------------------------------------------------------
# TEST: deep-translator Basic Translation
# -----------------------------------------------------------------------------
def test_basic_translation_google(GoogleTranslator):
    print_header("TEST 2A: GoogleTranslator Basic Translation")

    try:
        result = GoogleTranslator(source="en", target="tr").translate("Hello")
        print_result("GoogleTranslator Basic", "OK", f"Result: {result}")
        return True
    except Exception as e:
        print_result("GoogleTranslator Basic", "FAIL", "Translation failed", str(e))
        return False


# -----------------------------------------------------------------------------
# TEST: DeepL Basic Translation
# -----------------------------------------------------------------------------
def test_basic_translation_deepl(deepl_module, api_key):
    print_header("TEST 2B: DeepL Basic Translation")

    try:
        translator = deepl_module.Translator(api_key)
        result = translator.translate_text("Hello world", target_lang="TR")
        print_result("DeepL Basic", "OK", f"Result: {result.text}")
        return True
    except Exception as e:
        print_result("DeepL Basic", "FAIL", "DeepL translation failed", str(e))
        return False


# -----------------------------------------------------------------------------
# TEST: DeepL Multi-Language
# -----------------------------------------------------------------------------
def test_deepl_multiple_languages(deepl_module, api_key):
    print_header("TEST 3B: DeepL Multiple Languages")

    languages = {
        "Turkish": "TR",
        "German": "DE",
        "French": "FR",
        "Spanish": "ES",
        "Japanese": "JA"
    }

    translator = deepl_module.Translator(api_key)
    all_ok = True

    for lang_name, lang_code in languages.items():
        try:
            result = translator.translate_text("Good morning", target_lang=lang_code)
            print(f"   ✓ {lang_name} ({lang_code}): {result.text}")
        except Exception as e:
            print(f"   ✗ {lang_name} FAILED: {e}")
            all_ok = False

    print_result("DeepL Multi-Language", "OK" if all_ok else "PARTIAL",
                 "All languages OK" if all_ok else "Some languages failed")

    return all_ok


# -----------------------------------------------------------------------------
# TEST: DeepL Long Text
# -----------------------------------------------------------------------------
def test_deepl_long_text(deepl_module, api_key):
    print_header("TEST 4B: DeepL Long Text")

    long_text = (
        "This is a long text used to check if DeepL can translate it properly. "
        "DeepL usually handles long texts very well, preserving structure and meaning."
    )

    try:
        translator = deepl_module.Translator(api_key)
        result = translator.translate_text(long_text, target_lang="TR")

        if len(result.text) > 20:
            print_result("DeepL Long Text", "OK", "Long translation succeeded")
            return True
        else:
            print_result("DeepL Long Text", "FAIL", "Translation too short")
            return False

    except Exception as e:
        print_result("DeepL Long Text", "FAIL", "DeepL failed", str(e))
        return False


# -----------------------------------------------------------------------------
# Network Test
# -----------------------------------------------------------------------------
def test_network():
    print_header("TEST NETWORK")

    import socket
    try:
        socket.create_connection(("www.google.com", 80), timeout=5)
        print_result("Network", "OK", "Internet reachable")
        return True
    except Exception as e:
        print_result("Network", "FAIL", "No internet", str(e))
        return False


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main():
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "TRANSLATION SERVICE CHECK" + " " * 14 + "║")
    print("╚" + "═" * 58 + "╝")
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # 1A. deep-translator import
    google_ok, GoogleTranslator = test_import_deep_translator()
    results["google_import"] = google_ok

    # 1B. DeepL import
    deepl_ok, deepl_module = test_import_deepl()
    results["deepl_import"] = deepl_ok

    # 1C. DeepL API key
    if deepl_ok:
        api_ok, api_key = test_deepl_api_key()
    else:
        api_ok, api_key = False, None

    results["deepl_api"] = api_ok

    # GoogleTranslator tests
    if google_ok:
        results["google_basic"] = test_basic_translation_google(GoogleTranslator)
    else:
        results["google_basic"] = False

    # DeepL tests
    if deepl_ok and api_ok:
        results["deepl_basic"] = test_basic_translation_deepl(deepl_module, api_key)
        results["deepl_multi"] = test_deepl_multiple_languages(deepl_module, api_key)
        results["deepl_long"] = test_deepl_long_text(deepl_module, api_key)
    else:
        results["deepl_basic"] = False
        results["deepl_multi"] = False
        results["deepl_long"] = False

    # Network test
    results["network"] = test_network()

    # --------------------
    # Summary
    # --------------------
    print_header("SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n   Passed: {passed}/{total}\n")

    print("=" * 60)


if __name__ == "__main__":
    main()
