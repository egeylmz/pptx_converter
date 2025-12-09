import os
import json
from pathlib import Path
from typing import List, Dict, Optional

# ANTIALIAS patch for Pillow 10.0.0+ compatibility
try:
    from PIL import Image

    # ANTIALIAS was removed in Pillow 10.0.0+, LANCZOS should be used
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
except ImportError:
    pass

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import ImageDraw, ImageFont
import textwrap


def export_slides_to_images(pptx_file_path: str, output_dir: str, progress_callback=None,
                            slides_data: Optional[List[Dict]] = None) -> List[str]:
    """
    Exports PowerPoint slides to PNG images (using Windows COM interface).
    If slides_data is provided, it replaces texts with translated texts.

    Args:
        pptx_file_path: Path to the PowerPoint file
        output_dir: Directory where images will be saved
        progress_callback: Progress callback function
        slides_data: Translated text information (optional). Each dict should contain:
            - slide_number: int
            - original_blocks: List[str] (original text blocks)
            - translated_blocks: List[str] (translated text blocks)

    Returns:
        List of paths to the created image files
    """
    try:
        import win32com.client
    except ImportError:
        raise Exception(
            "pywin32 is not installed for slide export.\n"
            "To install: pip install pywin32"
        )

    os.makedirs(output_dir, exist_ok=True)
    image_paths = []

    # Create dictionary to index slides_data by slide_number
    slides_dict = {}
    if slides_data:
        for slide_info in slides_data:
            slide_num = slide_info.get('slide_number')
            if slide_num:
                slides_dict[slide_num] = slide_info

    try:
        # Start PowerPoint application
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        # In some PowerPoint versions hidden mode is not supported, leaving it visible
        try:
            powerpoint.Visible = 1  # Visible mode
        except:
            # Continue if Visible cannot be set
            pass

        # Open file
        presentation = powerpoint.Presentations.Open(os.path.abspath(pptx_file_path))
        slide_count = presentation.Slides.Count

        # Process each slide
        for slide_idx in range(1, slide_count + 1):
            if progress_callback:
                progress_callback(f'Exporting slide images: {slide_idx}/{slide_count}')

            slide = presentation.Slides(slide_idx)

            # If translated text info exists, replace texts
            if slide_idx in slides_dict:
                slide_info = slides_dict[slide_idx]
                original_blocks = slide_info.get('original_blocks', [])
                translated_blocks = slide_info.get('translated_blocks', [])

                if original_blocks and translated_blocks and len(original_blocks) == len(translated_blocks):
                    try:
                        # Get all shapes in the slide
                        text_shapes = []
                        for shape_idx in range(1, slide.Shapes.Count + 1):
                            shape = slide.Shapes(shape_idx)
                            # Find shapes containing text
                            if shape.HasTextFrame:
                                if shape.TextFrame.HasText:
                                    text_shapes.append(shape)

                        # Match and replace text blocks
                        block_idx = 0
                        for shape in text_shapes:
                            if block_idx < len(original_blocks) and block_idx < len(translated_blocks):
                                original_text = original_blocks[block_idx].strip()
                                translated_text = translated_blocks[block_idx].strip()

                                # Check text in shape (some characters might differ)
                                shape_text = shape.TextFrame.TextRange.Text.strip()

                                # Replace if text matches or is not empty
                                if original_text and translated_text:
                                    try:
                                        # Replace text
                                        shape.TextFrame.TextRange.Text = translated_text
                                        print(f"  → Slide {slide_idx}, block {block_idx + 1}: Text replaced")
                                    except Exception as text_error:
                                        print(
                                            f"  ⚠ Slide {slide_idx}, block {block_idx + 1}: Text could not be replaced: {str(text_error)}")

                                block_idx += 1

                        if block_idx > 0:
                            print(f"✓ Slide {slide_idx}: {block_idx} text blocks translated")
                    except Exception as replace_error:
                        print(f"⚠ Slide {slide_idx}: Text replacement error: {str(replace_error)}")
                        # Continue even if there is an error

            # Export slide as PNG (resolution: 1920x1080)
            image_path = os.path.join(output_dir, f'slide_{slide_idx:03d}.png')
            try:
                slide.Export(image_path, 'PNG', 1920, 1080)
                image_paths.append(image_path)
                print(f"✓ Slide {slide_idx} exported as image")
            except Exception as export_error:
                print(f"✗ Slide {slide_idx} export error: {str(export_error)}")

        # Close
        presentation.Close()
        powerpoint.Quit()

        # Clean up COM objects
        del presentation
        del powerpoint

        return image_paths

    except Exception as e:
        raise Exception(f"Slide export error: {str(e)}")


def create_slide_video(image_path: str, audio_path: Optional[str], duration: float) -> ImageClip:
    """
    Creates a video clip from an image and audio file.

    Args:
        image_path: Path to image file
        audio_path: Path to audio file (optional)
        duration: Video duration (seconds)

    Returns:
        VideoClip object
    """
    # Use actual duration if audio file exists, otherwise use duration parameter
    actual_duration = duration
    if audio_path and os.path.exists(audio_path):
        try:
            audio = AudioFileClip(audio_path)
            actual_duration = audio.duration  # Use actual audio duration
            audio.close()
        except Exception as e:
            print(f"Audio file could not be read, using duration parameter: {str(e)}")

    # Create video clip from image - for the duration of actual audio
    video = ImageClip(image_path)
    video = video.set_duration(actual_duration)  # Use actual duration
    video = video.set_fps(24)
    video = video.resize(newsize=(1920, 1080))  # Full HD

    # Add audio file
    if audio_path and os.path.exists(audio_path):
        try:
            audio = AudioFileClip(audio_path)
            video = video.set_audio(audio)
        except Exception as e:
            print(f"Error adding audio: {str(e)}, using only image")

    return video


def _fit_text_to_box(draw: ImageDraw.ImageDraw, text: str, font_path: Optional[str], box_width: int,
                     box_height: int) -> ImageFont.FreeTypeFont:
    """
    Adjusts font size to fit within the given box dimensions and returns the font.
    """
    # Initial font size guess (reasonable value based on screen height)
    font_size = 48

    # Helper to load fallback font
    def load_font(size: int):
        try:
            if font_path:
                return ImageFont.truetype(font_path, size=size)
            # Try common font names
            for candidate in [
                "arial.ttf",
                "Arial.ttf",
                "DejaVuSans.ttf",
                "LiberationSans-Regular.ttf",
            ]:
                try:
                    return ImageFont.truetype(candidate, size=size)
                except Exception:
                    continue
        except Exception:
            pass
        return ImageFont.load_default()

    # Function to wrap text
    def wrap_text(text_value: str, font_obj: ImageFont.FreeTypeFont, max_width: int) -> str:
        wrapped_lines = []
        for paragraph in text_value.splitlines():
            if not paragraph.strip():
                wrapped_lines.append("")
                continue
            words = paragraph.split()
            current = []
            for w in words:
                test = (" ".join(current + [w])).strip()
                w_width, _ = draw.textsize(test, font=font_obj)
                if w_width <= max_width or not current:
                    current.append(w)
                else:
                    wrapped_lines.append(" ".join(current))
                    current = [w]
            if current:
                wrapped_lines.append(" ".join(current))
        return "\n".join(wrapped_lines)

    # Fit to box by reducing font size
    for size in range(font_size, 12, -2):
        font = load_font(size)
        wrapped = wrap_text(text, font, box_width)
        w, h = draw.multiline_textsize(wrapped, font=font, spacing=8)
        if w <= box_width and h <= box_height:
            return font
    return load_font(12)


def create_overlay_image(base_image_path: str, text: str, output_path: str) -> str:
    """
    Overlays the translated text legibly on the bottom part of the slide image.
    """
    image = Image.open(base_image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    img_w, img_h = image.size

    # Text box dimensions (bottom section)
    margin = int(img_w * 0.05)
    box_width = img_w - 2 * margin
    box_height = int(img_h * 0.28)
    box_left = margin
    box_top = img_h - margin - box_height
    box_right = box_left + box_width
    box_bottom = box_top + box_height

    # Box background (semi-transparent black)
    overlay_color = (0, 0, 0, 180)
    # Separate layer for semi-transparent drawing
    overlay = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([box_left, box_top, box_right, box_bottom], fill=overlay_color)
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Font setting and text wrapping
    font = _fit_text_to_box(draw, text, font_path=None, box_width=box_width - margin, box_height=box_height - margin)

    # Re-wrap text and measure
    def wrap_with_font(text_value: str, font_obj: ImageFont.FreeTypeFont, max_width: int) -> str:
        wrapped_lines = []
        for paragraph in text_value.splitlines():
            if not paragraph.strip():
                wrapped_lines.append("")
                continue
            words = paragraph.split()
            current = []
            for w in words:
                test = (" ".join(current + [w])).strip()
                w_width, _ = draw.textsize(test, font=font_obj)
                if w_width <= max_width or not current:
                    current.append(w)
                else:
                    wrapped_lines.append(" ".join(current))
                    current = [w]
            if current:
                wrapped_lines.append(" ".join(current))
        return "\n".join(wrapped_lines)

    wrapped_text = wrap_with_font(text, font, box_width - margin)
    text_w, text_h = draw.multiline_textsize(wrapped_text, font=font, spacing=8)

    # Center text in box (horizontal), with some top padding
    text_x = box_left + (box_width - text_w) // 2
    text_y = box_top + (box_height - text_h) // 2

    # Text color: white
    draw.multiline_text((text_x, text_y), wrapped_text, font=font, fill=(255, 255, 255), spacing=8, align="center")

    image.save(output_path)
    return output_path


def create_video_from_json(json_file_path: str, pptx_file_path: str, progress_callback=None) -> str:
    """
    Creates the final video using information from the JSON file.

    Args:
        json_file_path: JSON file containing audio info
        pptx_file_path: Original PowerPoint file
        progress_callback: Progress callback function

    Returns:
        Path to the created video file
    """
    # Read JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    slides = data.get('slides', [])
    total_slides = len(slides)

    # Create working directories
    json_dir = os.path.dirname(os.path.abspath(json_file_path))
    json_basename = os.path.splitext(os.path.basename(json_file_path))[0]
    images_dir = os.path.join(json_dir, f'{json_basename}_images')

    # Export slide images (along with translated texts)
    if progress_callback:
        progress_callback('Converting PowerPoint slides to images (translating texts)...')

    # Send slides info to export function
    image_paths = export_slides_to_images(pptx_file_path, images_dir, progress_callback, slides_data=slides)

    # Create video clip for each slide
    video_clips = []
    for idx, slide in enumerate(slides, 1):
        slide_number = slide.get('slide_number', idx)
        audio_file = slide.get('audio_file')
        duration = slide.get('duration', 5.0)  # Default 5 seconds

        if progress_callback:
            progress_callback(f'Creating video: Slide {idx}/{total_slides}')

        # Find image file
        image_path = os.path.join(images_dir, f'slide_{slide_number:03d}.png')

        # If image doesn't exist, use the first image or skip
        if not os.path.exists(image_path) and image_paths:
            image_path = image_paths[slide_number - 1] if slide_number <= len(image_paths) else image_paths[0]

        if os.path.exists(image_path):
            # Overlay translated text on image
            translated_text = slide.get('translated_text', '') or ''
            overlay_image_path = image_path
            if translated_text.strip():
                overlay_image_path = os.path.join(images_dir, f'slide_{slide_number:03d}_overlay.png')
                try:
                    create_overlay_image(image_path, translated_text, overlay_image_path)
                except Exception as e:
                    print(f"Overlay could not be created, using original image: {str(e)}")
                    overlay_image_path = image_path

            clip = create_slide_video(overlay_image_path, audio_file, duration)
            video_clips.append(clip)
            print(f"✓ Slide {slide_number} video clip created")
        else:
            print(f"⚠ Slide {slide_number} image not found, skipping")

    if not video_clips:
        raise Exception("No video clips created!")

    # Merge all clips
    if progress_callback:
        progress_callback('Merging video clips...')

    print(f"{len(video_clips)} video clips being merged...")
    final_video = concatenate_videoclips(video_clips, method="compose")

    # Save video file
    output_video_path = json_file_path.replace('.json', '').replace('_with_audio', '') + '_video.mp4'

    if progress_callback:
        progress_callback(f'Saving video: {os.path.basename(output_video_path)}...')

    final_video.write_videofile(
        output_video_path,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=4
    )

    # Clean up clips
    for clip in video_clips:
        clip.close()
    final_video.close()

    print(f"✓ Video created: {output_video_path}")
    return output_video_path