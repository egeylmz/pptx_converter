import os
import json
from typing import List, Dict, Optional

# ANTIALIAS patch for Pillow 10.0.0+
try:
    from PIL import Image

    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
except ImportError:
    pass

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips


def export_slides_to_images(pptx_file_path: str, output_dir: str, progress_callback=None,
                            slides_data: Optional[List[Dict]] = None) -> List[str]:
    """
    Exports PowerPoint slides to PNG images, applying translations if available.
    """
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        raise Exception("pywin32 is not installed. pip install pywin32")

    os.makedirs(output_dir, exist_ok=True)
    image_paths = []

    try:
        # Initialize COM
        pythoncom.CoInitialize()
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        try:
            powerpoint.Visible = 1
        except:
            pass

        # Open file
        presentation = powerpoint.Presentations.Open(os.path.abspath(pptx_file_path))
        slide_count = presentation.Slides.Count

        print(f"\n{'=' * 60}")
        print(f"📸 EXPORTING TRANSLATED SLIDES")
        print(f"{'=' * 60}")

        # Export each slide
        for slide_idx in range(1, slide_count + 1):
            if progress_callback:
                progress_callback(f'Processing slide visual: {slide_idx}/{slide_count}')

            slide = presentation.Slides(slide_idx)

            # --- TRANSLATION REPLACEMENT LOGIC ---
            if slides_data and (slide_idx - 1) < len(slides_data):
                slide_info = slides_data[slide_idx - 1]
                translated_blocks = slide_info.get('translated_blocks', [])

                if translated_blocks:
                    print(f"   Applying translation to Slide {slide_idx}...")
                    block_index = 0
                    # Iterate shapes to find text and replace it
                    # Note: This relies on the order being the same as extraction
                    for shape in slide.Shapes:
                        if shape.HasTextFrame:
                            if shape.TextFrame.HasText:
                                if block_index < len(translated_blocks):
                                    # Replace text with translation
                                    try:
                                        new_text = translated_blocks[block_index]
                                        if new_text and new_text.strip():
                                            shape.TextFrame.TextRange.Text = new_text
                                    except Exception as e:
                                        print(f"   ⚠️ Could not replace text: {e}")
                                    block_index += 1
            # -------------------------------------

            # Export slide as PNG
            image_path = os.path.join(output_dir, f'slide_{slide_idx:03d}.png')
            try:
                slide.Export(image_path, 'PNG', 1920, 1080)
                image_paths.append(image_path)
                print(f"✅ Slide {slide_idx} exported")
            except Exception as export_error:
                print(f"❌ Slide {slide_idx} export error: {str(export_error)}")

        # CRITICAL: Mark as saved so it doesn't prompt to save changes (we want to discard translation changes)
        presentation.Saved = True
        presentation.Close()
        powerpoint.Quit()

        # Clean up COM
        del presentation
        del powerpoint

        return image_paths

    except Exception as e:
        raise Exception(f"Slide export error: {str(e)}")


def create_slide_video(image_path: str, audio_path: Optional[str], duration: float) -> ImageClip:
    """Creates a video clip from an image and audio file."""
    actual_duration = duration
    audio_clip = None

    # Check if audio file is valid
    if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 100:
        try:
            audio_clip = AudioFileClip(audio_path)
            actual_duration = audio_clip.duration
            print(f"✓ Audio loaded: {os.path.basename(audio_path)} ({actual_duration:.2f}s)")
        except Exception as e:
            print(f"⚠️ Could not load audio {os.path.basename(audio_path)}: {e}")
            actual_duration = max(duration, 3.0)
            audio_clip = None
    else:
        actual_duration = max(duration, 3.0)
        if audio_path:
            print(f"⚠️ Audio file missing or empty: {audio_path}")

    video = ImageClip(image_path)
    video = video.set_duration(actual_duration)
    video = video.set_fps(24)
    video = video.resize(newsize=(1920, 1080))

    # Attach audio to video clip
    if audio_clip is not None:
        video = video.set_audio(audio_clip)
        print(f"✓ Audio attached to slide")

    return video


def create_video_from_json(json_file_path: str, pptx_file_path: str, progress_callback=None) -> str:
    """Creates the final video using information from the JSON file."""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slides = data.get('slides', [])

    # Create working directories
    json_dir = os.path.dirname(os.path.abspath(json_file_path))
    json_basename = os.path.splitext(os.path.basename(json_file_path))[0]
    images_dir = os.path.join(json_dir, f'{json_basename}_images')

    # Export slides (Pass 'slides' data to enable text replacement)
    if progress_callback:
        progress_callback('Applying translations and exporting slides...')

    # CHANGED: Added slides=slides here
    image_paths = export_slides_to_images(pptx_file_path, images_dir, progress_callback, slides_data=slides)

    # Create video clip for each slide
    video_clips = []
    for idx, slide in enumerate(slides, 1):
        slide_number = slide.get('slide_number', idx)
        audio_file = slide.get('audio_file')
        duration = slide.get('duration', 5.0)

        image_path = os.path.join(images_dir, f'slide_{slide_number:03d}.png')
        if not os.path.exists(image_path) and image_paths:
            image_path = image_paths[slide_number - 1] if slide_number <= len(image_paths) else image_paths[0]

        if os.path.exists(image_path):
            if progress_callback:
                progress_callback(f'Creating clip for slide {idx}/{len(slides)}...')
            clip = create_slide_video(image_path, audio_file, duration)
            video_clips.append(clip)

    if not video_clips:
        raise Exception("No video clips created!")

    if progress_callback:
        progress_callback(f'Merging {len(video_clips)} video clips...')

    final_video = concatenate_videoclips(video_clips, method="compose")
    output_video_path = json_file_path.replace('.json', '').replace('_with_audio', '') + '_video.mp4'

    if progress_callback:
        progress_callback(f'Encoding final video (this may take a while)...')

    final_video.write_videofile(
        output_video_path,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=4,
        logger='bar'  # Show progress bar in terminal
    )

    for clip in video_clips:
        clip.close()
    final_video.close()

    return output_video_path