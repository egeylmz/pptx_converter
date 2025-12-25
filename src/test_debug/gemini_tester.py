import os
import sys
from pathlib import Path


def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║          GEMINI API CONNECTION DIAGNOSTIC            ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    # 1. FIND .ENV FILE
    current_dir = Path(__file__).parent
    project_root = current_dir.parent

    env_path_src = current_dir / ".env"
    env_path_root = project_root / ".env"

    found_path = None

    print("🔍 STEP 1: Locating .env file...")
    if env_path_src.exists():
        found_path = env_path_src
        print(f"   ✓ Found in src folder: {found_path}")
    elif env_path_root.exists():
        found_path = env_path_root
        print(f"   ✓ Found in project root: {found_path}")
    else:
        print("   ❌ No .env file found in 'src' or project root.")
        print("   -> Please ensure you have a file named exactly '.env'")

    # 2. READ API KEY
    print("\n🔍 STEP 2: Reading API Key...")
    api_key = None

    # Check Environment Variables first (System level)
    api_key = os.environ.get("GOOGLE_API_KEY")

    # If not in system env, try reading file manually to avoid library issues
    if not api_key and found_path:
        try:
            with open(found_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GOOGLE_API_KEY"):
                        # Split by first '=' only
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            # Clean up quotes and spaces
                            api_key = parts[1].strip().strip('"').strip("'")
                            print("   ✓ Read key directly from file")
                            break
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")

    if not api_key:
        print("   ❌ FATAL: Could not find GOOGLE_API_KEY.")
        return

    # Show masked key for verification
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "INVALID_LENGTH"
    print(f"   ✓ Key loaded: {masked_key}")

    # 3. TEST CONNECTION
    print("\n🔍 STEP 3: Testing Google API Connection...")

    # Try NEW SDK (google-genai)
    try:
        from google import genai
        print("   ℹ️  Attempting with NEW SDK (google-genai)...")
        client = genai.Client(api_key=api_key)

        # Test with the specific model you are using
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Reply with exactly three words: 'Connection is successful'"
        )
        print(f"\n✅ SUCCESS! Google Gemini responded:\n   \"{response.text.strip()}\"")
        return

    except ImportError:
        print("   ⚠️  New SDK not found. Trying fallback...")
    except Exception as e:
        print(f"   ❌ New SDK Failed: {e}")
        if "400" in str(e) or "INVALID_ARGUMENT" in str(e):
            print("      -> DIAGNOSIS: The API Key is incorrect or expired.")
            return

    # Try OLD SDK (google-generativeai) as fallback
    try:
        import google.generativeai as old_genai
        print("\n   ℹ️  Attempting with OLD SDK (google-generativeai)...")
        old_genai.configure(api_key=api_key)
        model = old_genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Reply with exactly three words: 'Connection is successful'")
        print(f"\n✅ SUCCESS! Google Gemini responded:\n   \"{response.text.strip()}\"")
        return

    except Exception as e:
        print(f"   ❌ Old SDK Failed: {e}")

    print("\n❌ DIAGNOSTIC FAILED: Could not connect with either SDK.")


if __name__ == "__main__":
    main()
    print("\n[Process finished]")