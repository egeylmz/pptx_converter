import sys
import os
import json
from datetime import datetime
import threading
import platform

# Load .env ONCE at the very beginning
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

import flet as ft

if platform.system() != 'Windows':
    print("⚠️ WARNING: This application requires Windows")
    sys.exit(1)

if sys.platform == 'win32':
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from pptx_reader import extract_text_from_pptx, get_slide_count
    from ppt_converter import convert_ppt_to_pptx, is_ppt_file
    from tts_generator import generate_audio_for_json
    from video_generator import create_video_from_json
    from ai_narrator import AITeacherNarrator, get_available_styles
    from enrichment_config import ENRICHMENT_LEVELS, get_enrichment_level_config

    # Try to import Cloud TTS
    try:
        from cloud_tts_generator import generate_audio_for_json_cloud

        CLOUD_TTS_AVAILABLE = True
        print("✓ Google Cloud TTS available")
    except ImportError:
        CLOUD_TTS_AVAILABLE = False
        print("⚠ Google Cloud TTS not available (using standard TTS)")

except ImportError as e:
    print(f"Warning: Backend modules not found ({e})")
    CLOUD_TTS_AVAILABLE = False


    def extract_text_from_pptx(path):
        return []


    def get_slide_count(path):
        return 0


    def convert_ppt_to_pptx(path):
        return path


    def is_ppt_file(path):
        return False


    def generate_audio_for_json(path, progress_callback=None):
        return path


    def create_video_from_json(path, video_path, progress_callback=None):
        return path


    def get_available_styles():
        return {"engaging": {"name": "Engaging", "description": "Default"}}


    class AITeacherNarrator:
        def __init__(self, *args, **kwargs): pass

        def narrate_slides(self, *args, **kwargs): return []

TRANSLATOR_AVAILABLE = False
try:
    from translator import translate_texts

    TRANSLATOR_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    TRANSLATOR_AVAILABLE = False


    def translate_texts(*args, **kwargs):
        raise Exception("Translation feature is not available")


def main(page: ft.Page):
    page.title = "Presentation to Lecture"
    page.padding = 0
    page.window_width = 1100
    page.window_height = 950
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0F172A"
    page.fonts = {
        "RobotoMono": "https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500&display=swap",
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap"
    }
    page.theme = ft.Theme(font_family="Inter")

    selected_file = {"path": None, "converted_pptx": None}

    # Colors
    COLOR_BG_PAGE = "#0F172A"
    COLOR_PRIMARY = "#6366F1"
    COLOR_ACCENT = "#818CF8"
    COLOR_TEXT_MAIN = "#F8FAFC"
    COLOR_TEXT_SUB = "#94A3B8"
    COLOR_SUCCESS = "#10B981"
    COLOR_ERROR = "#EF4444"
    COLOR_WARNING = "#F59E0B"
    COLOR_BG_TERMINAL = "#020617"

    language_map = {
        'English': 'en', 'Turkish': 'tr', 'German': 'de', 'French': 'fr',
        'Spanish': 'es', 'Italian': 'it', 'Russian': 'ru', 'Japanese': 'ja',
        'Korean': 'ko', 'Chinese (Simplified)': 'zh-CN'
    }

    narration_styles = get_available_styles()

    def add_log(message, color=COLOR_TEXT_SUB):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = ft.Text(f"[{timestamp}] > {message}", font_family="RobotoMono",
                           size=12, color=color, selectable=True)
        terminal_list.controls.append(log_line)
        terminal_list.update()
        terminal_list.scroll_to(offset=-1, duration=100)

    def update_status(message, style="info"):
        styles = {
            "info": {"color": COLOR_ACCENT, "bg": "#1E1B4B", "icon": ft.Icons.INFO_OUTLINE},
            "success": {"color": COLOR_SUCCESS, "bg": "#064E3B", "icon": ft.Icons.CHECK_CIRCLE_OUTLINE},
            "warning": {"color": COLOR_WARNING, "bg": "#451A03", "icon": ft.Icons.WARNING_AMBER_ROUNDED},
            "error": {"color": COLOR_ERROR, "bg": "#450A0A", "icon": ft.Icons.ERROR_OUTLINE},
        }
        s = styles.get(style, styles["info"])
        status_icon.name = s["icon"]
        status_icon.color = s["color"]
        status_text.value = message
        status_text.color = s["color"]
        status_container.bgcolor = s["bg"]
        status_container.border = ft.border.all(1, s["color"])
        status_container.visible = True
        status_container.update()
        add_log(message, s["color"])

    def reset_all_ui():
        selected_file["path"] = None
        selected_file["converted_pptx"] = None
        upload_icon.name = ft.Icons.CLOUD_UPLOAD_OUTLINED
        upload_icon.color = COLOR_PRIMARY
        upload_text.value = "Drop File or Click"
        upload_text.color = COLOR_TEXT_MAIN
        upload_subtext.value = ".pptx or .ppt files supported"
        upload_container.border = ft.border.all(1, "#334155")
        upload_container.bgcolor = "#0F172A"
        upload_container.update()
        convert_btn.disabled = True
        convert_btn.content.controls[1].value = "START CONVERSION"
        convert_btn.style.bgcolor = {ft.ControlState.DISABLED: "#1E293B", "": COLOR_PRIMARY}
        convert_btn.content.color = "#94A3B8"
        convert_btn.update()
        terminal_list.controls.clear()
        terminal_container.visible = False
        terminal_container.update()
        status_container.visible = False
        status_container.update()
        result_container.visible = False
        result_container.update()
        lang_dropdown.value = "English"
        style_dropdown.value = "engaging"
        enrichment_dropdown.value = "none"
        voice_quality_dropdown.value = "cloud" if CLOUD_TTS_AVAILABLE else "gtts"
        voice_gender_dropdown.value = "MALE"
        lang_dropdown.update()
        style_dropdown.update()
        enrichment_dropdown.update()
        voice_quality_dropdown.update()
        voice_gender_dropdown.update()
        page.update()

    def on_file_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        file_path = os.path.normpath(e.files[0].path)
        converted_file = None
        upload_icon.name = ft.Icons.INSERT_DRIVE_FILE
        upload_text.value = "Analyzing File..."
        upload_subtext.value = "Checking compatibility..."
        upload_container.update()
        terminal_list.controls.clear()
        add_log(f"File selected: {file_path}", COLOR_TEXT_MAIN)

        if is_ppt_file(file_path):
            try:
                update_status('Converting old .ppt format...', "warning")
                converted_file = convert_ppt_to_pptx(file_path)
                file_path = converted_file
                add_log("Legacy .ppt file converted to .pptx", COLOR_SUCCESS)
            except Exception as ex:
                update_status(f"Conversion Error: {str(ex)}", "error")
                reset_upload_ui()
                return

        if not os.path.exists(file_path):
            update_status(f'Error: File not found', "error")
            reset_upload_ui()
            return

        try:
            slide_count = get_slide_count(file_path)
            selected_file["path"] = file_path
            selected_file["converted_pptx"] = converted_file
            file_name = os.path.basename(file_path)
            upload_icon.name = ft.Icons.CHECK_CIRCLE
            upload_icon.color = COLOR_SUCCESS
            upload_text.value = file_name
            upload_text.color = COLOR_SUCCESS
            upload_subtext.value = f"{slide_count} Slides Found"
            upload_container.border = ft.border.all(2, COLOR_SUCCESS)
            upload_container.bgcolor = "#064E3B"
            upload_container.update()
            add_log(f"Ready to process {slide_count} slides.", COLOR_SUCCESS)
            convert_btn.disabled = False
            convert_btn.style.bgcolor = COLOR_PRIMARY
            convert_btn.content.color = "#FFFFFF"
            convert_btn.update()
        except Exception as ex:
            update_status(f"Error: {str(ex)}", "error")
            reset_upload_ui()

    def reset_upload_ui():
        upload_icon.name = ft.Icons.CLOUD_UPLOAD_OUTLINED
        upload_icon.color = COLOR_PRIMARY
        upload_text.value = "Drop File or Click"
        upload_text.color = COLOR_TEXT_MAIN
        upload_subtext.value = ".pptx or .ppt files supported"
        upload_container.border = ft.border.all(1, "#334155")
        upload_container.bgcolor = "#0F172A"
        upload_container.update()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    def start_conversion_thread():
        if not selected_file["path"]:
            return

        lang_code = language_map[lang_dropdown.value]
        narration_style = style_dropdown.value
        enrichment_level = enrichment_dropdown.value

        convert_btn.disabled = True
        convert_btn.content.controls[1].value = "PROCESSING..."
        convert_btn.update()
        terminal_container.visible = True
        terminal_container.update()
        result_container.visible = False
        result_container.update()

        try:
            # 1. Extract
            add_log('📖 Reading PowerPoint data...', COLOR_ACCENT)
            slides_data = extract_text_from_pptx(selected_file["path"])
            add_log(f"✓ Extracted text from {len(slides_data)} slides.", COLOR_SUCCESS)

            # 2. AI Narration with selected style (ALWAYS run)
            style_name = narration_styles[narration_style]['name']
            add_log(f'🤖 Generating AI narration ({style_name})...', COLOR_ACCENT)

            if enrichment_level != "none":
                add_log(f"🔬 Content enrichment: {enrichment_level}", COLOR_ACCENT)

            try:
                style_temp = narration_styles[narration_style]['temperature']
                narrator = AITeacherNarrator(
                    temperature=style_temp,
                    style=narration_style,
                    enrichment_level=enrichment_level
                )
                slides_data = narrator.narrate_slides(
                    slides_data,
                    progress_callback=lambda msg: add_log(msg, COLOR_ACCENT)
                )
                add_log(f"✓ Context-aware narration generated", COLOR_SUCCESS)
            except Exception as e:
                add_log(f"⚠ AI narration failed: {str(e)}", COLOR_WARNING)
                add_log("Using original text as fallback", COLOR_WARNING)
                for slide in slides_data:
                    slide['ai_narration'] = slide.get('text', '')

            # 3. Translation
            if TRANSLATOR_AVAILABLE and lang_code != 'en':
                add_log(f'🌐 Translating to {lang_code}...', COLOR_ACCENT)

                # FIXED: Use enriched text if available, otherwise AI narration
                for slide in slides_data:
                    slide['text'] = slide.get('enriched_text',
                                              slide.get('ai_narration',
                                                        slide.get('text', '')))

                try:
                    translated_slides = translate_texts(slides_data, lang_code,
                                                        progress_callback=lambda msg: add_log(msg))
                except Exception as e:
                    add_log(f"⚠ Translation failed: {str(e)}", COLOR_ERROR)
                    translated_slides = slides_data
                    for slide in translated_slides:
                        slide['translated_text'] = slide.get('enriched_text',
                                                             slide.get('ai_narration',
                                                                       slide.get('text', '')))
            else:
                translated_slides = slides_data
                for slide in translated_slides:
                    slide['translated_text'] = slide.get('enriched_text',
                                                         slide.get('ai_narration',
                                                                   slide.get('text', '')))
                if lang_code == 'en':
                    add_log("✓ Target language is English, using narration directly.", COLOR_SUCCESS)

            # 4. Validate
            for idx, slide in enumerate(translated_slides):
                if not slide.get('translated_text'):
                    slide['translated_text'] = slide.get('text', f'Slide {idx + 1}')
                if not slide.get('slide_number'):
                    slide['slide_number'] = idx + 1

            # 5. Save JSON
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            os.makedirs(output_dir, exist_ok=True)
            source_filename = os.path.splitext(os.path.basename(selected_file["path"]))[0]
            json_filename = f"{source_filename}_{lang_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_filepath = os.path.join(output_dir, json_filename)

            output_data = {
                "source_file": os.path.basename(selected_file["path"]),
                "target_language": lang_code,
                "narration_style": narration_style,
                "enrichment_level": enrichment_level,
                "translation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_slides": len(translated_slides),
                "slides": [
                    {
                        "slide_number": slide.get("slide_number"),
                        "original_text": slide.get("original_text", slide.get("text", "")),
                        "ai_narration": slide.get("ai_narration", ""),
                        "enriched_text": slide.get("enriched_text", ""),
                        "translated_text": slide.get("translated_text", ""),
                        "translated_blocks": slide.get("translated_blocks", []),
                        "audio_file": None,
                        "duration": None
                    }
                    for slide in translated_slides
                ]
            }

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            add_log(f"✓ Data saved to {json_filename}", COLOR_SUCCESS)

            # 6. TTS & Video
            use_cloud_tts = voice_quality_dropdown.value == "cloud" and CLOUD_TTS_AVAILABLE
            voice_gender = voice_gender_dropdown.value

            if use_cloud_tts:
                add_log('🎙️ Starting Audio Generation (Google Cloud TTS - Premium)...', COLOR_ACCENT)
                try:
                    audio_json_path = generate_audio_for_json_cloud(
                        json_filepath,
                        progress_callback=lambda msg: add_log(msg),
                        gender=voice_gender
                    )
                except Exception as e:
                    add_log(f'⚠ Cloud TTS failed: {str(e)}, falling back to gTTS', COLOR_WARNING)
                    audio_json_path = generate_audio_for_json(
                        json_filepath,
                        progress_callback=lambda msg: add_log(msg)
                    )
            else:
                add_log('🎙️ Starting Audio Generation (gTTS - Free)...', COLOR_ACCENT)
                audio_json_path = generate_audio_for_json(
                    json_filepath,
                    progress_callback=lambda msg: add_log(msg)
                )

            add_log('🎬 Rendering Video (FFmpeg)...', COLOR_ACCENT)
            video_path = create_video_from_json(audio_json_path, selected_file["path"],
                                                progress_callback=lambda msg: add_log(msg))

            # 7. Cleanup
            if selected_file["converted_pptx"]:
                try:
                    os.remove(selected_file["converted_pptx"])
                    add_log("🧹 Cleaned up temporary .ppt conversion file", COLOR_TEXT_SUB)
                except:
                    pass

            update_status("✅ Task Complete!", "success")
            result_filename.value = os.path.basename(video_path)
            result_path.value = video_path
            result_container.visible = True
            result_container.update()
            convert_btn.disabled = False
            convert_btn.content.controls[1].value = "NEW CONVERSION"
            convert_btn.content.controls[0].name = ft.Icons.REFRESH
            convert_btn.update()

        except Exception as e:
            import traceback
            traceback.print_exc()
            update_status(f"❌ Critical Error: {str(e)}", "error")
            add_log(str(e), COLOR_ERROR)
            convert_btn.disabled = False
            convert_btn.content.controls[1].value = "RETRY"
            convert_btn.update()

    def start_conversion(e):
        button_text = convert_btn.content.controls[1].value
        if button_text in ["NEW CONVERSION", "RETRY"]:
            reset_all_ui()
            return
        threading.Thread(target=start_conversion_thread, daemon=True).start()

    # ==================== UI COMPONENTS ====================

    header = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.AUTO_AWESOME_MOTION, color=COLOR_PRIMARY, size=35),
            ft.Column([
                ft.Text("PRESENTATION TO LECTURE", size=24, weight=ft.FontWeight.BOLD,
                        color=COLOR_TEXT_MAIN, font_family="Inter"),
                ft.Text("AI-Powered Video Lecture Generator", size=12, color=COLOR_TEXT_SUB,
                        font_family="RobotoMono"),
            ], spacing=2)
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.padding.only(bottom=20)
    )

    upload_icon = ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=50, color=COLOR_PRIMARY)
    upload_text = ft.Text("Drop File or Click", size=16, weight=ft.FontWeight.BOLD,
                          color=COLOR_TEXT_MAIN)
    upload_subtext = ft.Text(".pptx or .ppt files supported", size=12, color=COLOR_TEXT_SUB)

    def on_hover_upload(e):
        e.control.scale = 1.02 if e.data == "true" else 1.0
        e.control.border = ft.border.all(1, COLOR_PRIMARY if e.data == "true" else "#334155")
        e.control.update()

    upload_container = ft.Container(
        content=ft.Column([upload_icon, upload_text, upload_subtext],
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                          alignment=ft.MainAxisAlignment.CENTER, spacing=8),
        padding=40, bgcolor="#0F172A", border=ft.border.all(1, "#334155"),
        border_radius=16, ink=True,
        on_click=lambda _: file_picker.pick_files(allowed_extensions=["pptx", "ppt"]),
        on_hover=on_hover_upload, animate_scale=ft.Animation(200, "easeOut"),
        height=200, width=550, alignment=ft.alignment.center
    )

    style_options = []
    for key, config in narration_styles.items():
        style_options.append(
            ft.dropdown.Option(
                key=key,
                text=f"{config['name']} - {config['description']}"
            )
        )

    style_dropdown = ft.Dropdown(
        label="Narration Style",
        hint_text="Choose how AI explains the content",
        options=style_options,
        value="engaging",
        width=550,
        bgcolor="#0F172A",
        border_color="#334155",
        color=COLOR_TEXT_MAIN,
        focused_border_color=COLOR_PRIMARY,
        content_padding=18,
        text_size=14
    )

    enrichment_options = []
    for key, config in ENRICHMENT_LEVELS.items():
        enrichment_options.append(
            ft.dropdown.Option(
                key=key,
                text=f"{config['name']} - {config['description']}"
            )
        )

    enrichment_dropdown = ft.Dropdown(
        label="Content Enrichment Level",
        hint_text="Add extra information to narrations",
        options=enrichment_options,
        value="none",
        width=550,
        bgcolor="#0F172A",
        border_color="#334155",
        color=COLOR_TEXT_MAIN,
        focused_border_color=COLOR_PRIMARY,
        content_padding=18,
        text_size=14
    )

    voice_quality_dropdown = ft.Dropdown(
        label="Voice Quality",
        hint_text="Choose TTS engine",
        options=[
            ft.dropdown.Option("cloud", "Google Cloud TTS (Premium Neural Voices)"),
            ft.dropdown.Option("gtts", "gTTS (Free, Basic Quality)")
        ],
        value="cloud" if CLOUD_TTS_AVAILABLE else "gtts",
        width=550,
        bgcolor="#0F172A",
        border_color="#334155",
        color=COLOR_TEXT_MAIN,
        focused_border_color=COLOR_PRIMARY,
        content_padding=18,
        text_size=14,
        disabled=not CLOUD_TTS_AVAILABLE
    )

    voice_gender_dropdown = ft.Dropdown(
        label="Voice Gender (Cloud TTS only)",
        options=[
            ft.dropdown.Option("MALE", "Male Voice"),
            ft.dropdown.Option("FEMALE", "Female Voice")
        ],
        value="MALE",
        width=550,
        bgcolor="#0F172A",
        border_color="#334155",
        color=COLOR_TEXT_MAIN,
        focused_border_color=COLOR_PRIMARY,
        content_padding=18,
        text_size=14
    )

    lang_dropdown = ft.Dropdown(
        label="Target Language",
        options=[ft.dropdown.Option(l) for l in language_map.keys()],
        value="English",
        width=550,
        bgcolor="#0F172A",
        border_color="#334155",
        color=COLOR_TEXT_MAIN,
        focused_border_color=COLOR_PRIMARY,
        content_padding=18,
        text_size=15
    )

    convert_btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED),
                        ft.Text("START CONVERSION", weight=ft.FontWeight.BOLD)],
                       alignment=ft.MainAxisAlignment.CENTER),
        style=ft.ButtonStyle(color="#94A3B8",
                             bgcolor={ft.ControlState.DISABLED: "#1E293B", "": COLOR_PRIMARY},
                             shape=ft.RoundedRectangleBorder(radius=8), padding=22),
        width=550, disabled=True, on_click=start_conversion
    )

    terminal_list = ft.ListView(expand=True, spacing=2, auto_scroll=True, padding=10)

    terminal_container = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("TERMINAL OUTPUT", size=10, weight=ft.FontWeight.BOLD,
                                color="#475569"),
                padding=ft.padding.only(left=10, top=5)
            ),
            terminal_list
        ]),
        bgcolor=COLOR_BG_TERMINAL, border_radius=8,
        border=ft.border.all(1, "#334155"),
        width=550, height=150, visible=False
    )

    status_icon = ft.Icon(ft.Icons.INFO_OUTLINE, size=18)
    status_text = ft.Text("", size=13, weight=ft.FontWeight.W_500)
    status_container = ft.Container(
        content=ft.Row([status_icon, status_text], alignment=ft.MainAxisAlignment.CENTER),
        padding=12, border_radius=50, visible=False, width=550
    )

    result_filename = ft.Text("", weight=ft.FontWeight.BOLD, size=15,
                              color=COLOR_TEXT_MAIN, font_family="RobotoMono")
    result_path = ft.Text("", size=11, color=COLOR_TEXT_SUB, selectable=True)

    result_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.ROCKET_LAUNCH_ROUNDED, color=COLOR_SUCCESS, size=40),
            ft.Text("RENDERING COMPLETE", size=16, weight=ft.FontWeight.BOLD,
                    color=COLOR_SUCCESS, font_family="Inter"),
            ft.Divider(height=20, color="transparent"),
            result_filename,
            ft.Container(height=5),
            ft.ElevatedButton("OPEN FOLDER", icon=ft.Icons.FOLDER_OPEN,
                              on_click=lambda _: os.startfile(os.path.dirname(result_path.value))
                              if sys.platform == 'win32' else None,
                              style=ft.ButtonStyle(color=COLOR_SUCCESS, bgcolor="#064E3B",
                                                   shape=ft.RoundedRectangleBorder(radius=8)))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#1A10B981", border=ft.border.all(1, COLOR_SUCCESS),
        border_radius=12, padding=25, width=550, visible=False
    )

    main_card = ft.Container(
        content=ft.Column([
            header,
            ft.Divider(height=20, color="transparent"),
            upload_container,
            ft.Divider(height=20, color="transparent"),
            style_dropdown,
            ft.Divider(height=10, color="transparent"),
            enrichment_dropdown,
            ft.Divider(height=10, color="transparent"),
            voice_quality_dropdown,
            ft.Divider(height=10, color="transparent"),
            voice_gender_dropdown,
            ft.Divider(height=10, color="transparent"),
            lang_dropdown,
            ft.Divider(height=10, color="transparent"),
            convert_btn,
            ft.Divider(height=20, color="transparent"),
            status_container,
            ft.Divider(height=10, color="transparent"),
            terminal_container,
            ft.Divider(height=10, color="transparent"),
            result_container
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.HIDDEN),
        bgcolor="#D91E293B", blur=ft.Blur(10, 10, ft.BlurTileMode.MIRROR),
        padding=40, border_radius=20, border=ft.border.all(1, "#334155"),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=20,
                            color="#000000", offset=ft.Offset(0, 10)),
        width=700, alignment=ft.alignment.center
    )

    page.add(ft.Container(content=main_card, alignment=ft.alignment.center,
                          expand=True, bgcolor=COLOR_BG_PAGE))


if __name__ == '__main__':
    ft.app(target=main)