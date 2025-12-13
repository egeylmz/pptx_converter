"""
Debug Script for Video Generation Issues
Run this to identify exactly where the pipeline is failing
"""
import os
import json
from pathlib import Path


def debug_video_generation(output_dir="output"):
    """Debug why videos are 261 bytes (corrupted)"""

    print("=" * 80)
    print("VIDEO GENERATION DEBUG TOOL")
    print("=" * 80)
    print()

    if not os.path.exists(output_dir):
        print(f"❌ Output directory '{output_dir}' not found!")
        return

    # Find most recent JSON file with audio
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    if not json_files:
        print("❌ No JSON files found. Run a conversion first.")
        return

    # Look for audio JSON
    audio_json = [f for f in json_files if 'with_audio' in f]
    if not audio_json:
        print("⚠️  No 'with_audio' JSON found. TTS might not have completed.")
        print("   Available JSON files:")
        for f in json_files:
            print(f"   - {f}")
        return

    latest_audio_json = sorted(audio_json, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))[-1]
    json_path = os.path.join(output_dir, latest_audio_json)

    print(f"Analyzing: {latest_audio_json}")
    print("-" * 80)
    print()

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slides = data.get('slides', [])
    total_slides = len(slides)

    print(f"Total slides: {total_slides}")
    print()

    # Check each component
    issues = []

    # 1. Check Audio Files
    print("1. CHECKING AUDIO FILES")
    print("-" * 80)
    audio_ok = 0
    audio_missing = 0
    audio_empty = 0

    for slide in slides:
        slide_num = slide.get('slide_number')
        audio_file = slide.get('audio_file')
        duration = slide.get('duration', 0)

        if not audio_file:
            print(f"  ✗ Slide {slide_num}: No audio_file specified in JSON")
            audio_missing += 1
            continue

        if not os.path.exists(audio_file):
            print(f"  ✗ Slide {slide_num}: Audio file missing: {audio_file}")
            audio_missing += 1
        else:
            size = os.path.getsize(audio_file)
            if size == 0:
                print(f"  ✗ Slide {slide_num}: Audio file is empty (0 bytes)")
                audio_empty += 1
            elif size < 100:
                print(f"  ✗ Slide {slide_num}: Audio file too small ({size} bytes)")
                audio_empty += 1
            else:
                audio_ok += 1

    print(f"\nAudio Summary:")
    print(f"  ✓ Valid: {audio_ok}")
    print(f"  ✗ Missing: {audio_missing}")
    print(f"  ✗ Empty/Invalid: {audio_empty}")

    if audio_missing > 0 or audio_empty > 0:
        issues.append("Audio files are missing or empty")

    print()

    # 2. Check Image Files
    print("2. CHECKING IMAGE FILES")
    print("-" * 80)

    json_basename = os.path.splitext(latest_audio_json)[0].replace('_with_audio', '')
    images_dir = os.path.join(output_dir, f'{json_basename}_images')

    if not os.path.exists(images_dir):
        print(f"  ✗ Images directory not found: {images_dir}")
        issues.append("Slide images were not exported")
    else:
        image_files = [f for f in os.listdir(images_dir) if f.endswith('.png')]
        print(f"  ✓ Images directory exists: {images_dir}")
        print(f"  ✓ Found {len(image_files)} PNG files")

        if len(image_files) < total_slides:
            print(f"  ⚠️  Expected {total_slides} images, found {len(image_files)}")
            issues.append("Not all slides were exported as images")

    print()

    # 3. Check if FFmpeg is working
    print("3. CHECKING FFMPEG")
    print("-" * 80)

    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                                capture_output=True,
                                text=True,
                                timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"  ✓ FFmpeg installed: {version_line}")
        else:
            print(f"  ✗ FFmpeg returned error code: {result.returncode}")
            issues.append("FFmpeg is not working correctly")
    except FileNotFoundError:
        print(f"  ✗ FFmpeg not found in PATH")
        issues.append("FFmpeg is not installed or not in PATH")
    except subprocess.TimeoutExpired:
        print(f"  ✗ FFmpeg command timed out")
        issues.append("FFmpeg is not responding")

    print()

    # 4. Test creating a simple video
    print("4. TESTING SIMPLE VIDEO CREATION")
    print("-" * 80)

    try:
        from moviepy.editor import ColorClip, AudioFileClip
        import tempfile

        # Create a simple 2-second red video
        test_video_path = os.path.join(output_dir, 'test_video.mp4')

        print("  Creating test video (2-second red clip)...")
        clip = ColorClip(size=(640, 480), color=(255, 0, 0), duration=2)
        clip = clip.set_fps(24)

        clip.write_videofile(
            test_video_path,
            fps=24,
            codec='libx264',
            audio=False,
            verbose=False,
            logger=None
        )

        clip.close()

        # Check if it was created
        if os.path.exists(test_video_path):
            size = os.path.getsize(test_video_path)
            if size > 1000:
                print(f"  ✓ Test video created successfully ({size} bytes)")
                print(f"  ✓ MoviePy and FFmpeg are working!")
            else:
                print(f"  ✗ Test video too small ({size} bytes)")
                issues.append("MoviePy cannot create valid videos")
        else:
            print(f"  ✗ Test video was not created")
            issues.append("MoviePy failed to create video")

    except Exception as e:
        print(f"  ✗ Error creating test video: {str(e)}")
        issues.append(f"MoviePy error: {str(e)}")

    print()

    # 5. Check existing MP4 files
    print("5. CHECKING EXISTING MP4 FILES")
    print("-" * 80)

    mp4_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4') and f != 'test_video.mp4']

    if not mp4_files:
        print("  ⚠️  No MP4 files found (excluding test)")
    else:
        for mp4 in mp4_files:
            mp4_path = os.path.join(output_dir, mp4)
            size = os.path.getsize(mp4_path)

            if size == 261:
                print(f"  ✗ {mp4}: {size} bytes (CORRUPTED - typical header-only file)")
            elif size < 1000:
                print(f"  ✗ {mp4}: {size} bytes (TOO SMALL)")
            else:
                print(f"  ✓ {mp4}: {size:,} bytes ({size / (1024 * 1024):.2f} MB)")

    print()
    print("=" * 80)
    print("DIAGNOSIS")
    print("=" * 80)

    if not issues:
        print("\n✓ No obvious issues detected!")
        print("\nBut since your MP4s are 261 bytes, the issue might be:")
        print("1. Video encoding is failing silently")
        print("2. Check the console output during video creation for errors")
        print("3. The video_generator.py might be catching and suppressing errors")
    else:
        print("\n⚠️  ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")

    print("\n" + "=" * 80)
    print("RECOMMENDED ACTIONS:")
    print("=" * 80)

    print("\n1. If audio files are missing/empty:")
    print("   - TTS generation failed")
    print("   - Check gTTS installation: pip install --upgrade gTTS")
    print("   - Check internet connection (gTTS needs internet)")

    print("\n2. If images are missing:")
    print("   - PowerPoint slide export failed")
    print("   - Check pywin32 installation: pip install --upgrade pywin32")
    print("   - Make sure PowerPoint is installed on your system")

    print("\n3. If FFmpeg issues:")
    print("   - Install FFmpeg: https://ffmpeg.org/download.html")
    print("   - Add FFmpeg to PATH")
    print("   - Restart your terminal/IDE after installing")

    print("\n4. If MoviePy issues:")
    print("   - Reinstall: pip uninstall moviepy && pip install moviepy")
    print("   - Install: pip install imageio-ffmpeg")

    print("\n5. Check video_generator.py for caught exceptions:")
    print("   - Look for try/except blocks that might be hiding errors")
    print("   - Add print statements before write_videofile() call")


if __name__ == "__main__":
    debug_video_generation()