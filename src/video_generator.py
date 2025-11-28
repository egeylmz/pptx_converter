import os
import json
from pathlib import Path
from typing import List, Dict, Optional

# Pillow 10.0.0+ uyumluluğu için ANTIALIAS patch'i
try:
    from PIL import Image
    # Pillow 10.0.0+ sürümlerinde ANTIALIAS kaldırıldı, LANCZOS kullanılmalı
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
except ImportError:
    pass

from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import ImageDraw, ImageFont
import textwrap


def export_slides_to_images(pptx_file_path: str, output_dir: str, progress_callback=None, slides_data: Optional[List[Dict]] = None) -> List[str]:
    """
    PowerPoint slaytlarını PNG görsellerine export eder (Windows COM interface kullanarak).
    Eğer slides_data verilirse, metinleri çevrilmiş metinlerle değiştirir.
    
    Args:
        pptx_file_path: PowerPoint dosyasının yolu
        output_dir: Görsellerin kaydedileceği klasör
        progress_callback: İlerleme callback fonksiyonu
        slides_data: Çevrilmiş metin bilgileri (opsiyonel). Her dict şunları içermeli:
            - slide_number: int
            - original_blocks: List[str] (orijinal metin blokları)
            - translated_blocks: List[str] (çevrilmiş metin blokları)
        
    Returns:
        Oluşturulan görsel dosyalarının yolları listesi
    """
    try:
        import win32com.client
    except ImportError:
        raise Exception(
            "Slayt export için pywin32 kurulu değil.\n"
            "Kurulum için: pip install pywin32"
        )
    
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    
    # slides_data'yı slide_number'a göre index'lemek için dictionary oluştur
    slides_dict = {}
    if slides_data:
        for slide_info in slides_data:
            slide_num = slide_info.get('slide_number')
            if slide_num:
                slides_dict[slide_num] = slide_info
    
    try:
        # PowerPoint uygulamasını başlat
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        # Bazı PowerPoint sürümlerinde gizli mod desteklenmiyor, görünür bırakıyoruz
        try:
            powerpoint.Visible = 1  # Görünür mod
        except:
            # Visible ayarlanamıyorsa devam et
            pass
        
        # Dosyayı aç
        presentation = powerpoint.Presentations.Open(os.path.abspath(pptx_file_path))
        slide_count = presentation.Slides.Count
        
        # Her slaytı işle
        for slide_idx in range(1, slide_count + 1):
            if progress_callback:
                progress_callback(f'Slayt görselleri export ediliyor: {slide_idx}/{slide_count}')
            
            slide = presentation.Slides(slide_idx)
            
            # Eğer çevrilmiş metin bilgisi varsa, metinleri değiştir
            if slide_idx in slides_dict:
                slide_info = slides_dict[slide_idx]
                original_blocks = slide_info.get('original_blocks', [])
                translated_blocks = slide_info.get('translated_blocks', [])
                
                if original_blocks and translated_blocks and len(original_blocks) == len(translated_blocks):
                    try:
                        # Slayttaki tüm shape'leri al
                        text_shapes = []
                        for shape_idx in range(1, slide.Shapes.Count + 1):
                            shape = slide.Shapes(shape_idx)
                            # Text içeren shape'leri bul
                            if shape.HasTextFrame:
                                if shape.TextFrame.HasText:
                                    text_shapes.append(shape)
                        
                        # Metin bloklarını eşleştir ve değiştir
                        block_idx = 0
                        for shape in text_shapes:
                            if block_idx < len(original_blocks) and block_idx < len(translated_blocks):
                                original_text = original_blocks[block_idx].strip()
                                translated_text = translated_blocks[block_idx].strip()
                                
                                # Shape'teki metni kontrol et (bazı karakterler farklı olabilir)
                                shape_text = shape.TextFrame.TextRange.Text.strip()
                                
                                # Metin eşleşiyorsa veya boş değilse değiştir
                                if original_text and translated_text:
                                    try:
                                        # Metni değiştir
                                        shape.TextFrame.TextRange.Text = translated_text
                                        print(f"  → Slayt {slide_idx}, blok {block_idx + 1}: Metin değiştirildi")
                                    except Exception as text_error:
                                        print(f"  ⚠ Slayt {slide_idx}, blok {block_idx + 1}: Metin değiştirilemedi: {str(text_error)}")
                                
                                block_idx += 1
                        
                        if block_idx > 0:
                            print(f"✓ Slayt {slide_idx}: {block_idx} metin bloğu çevrildi")
                    except Exception as replace_error:
                        print(f"⚠ Slayt {slide_idx}: Metin değiştirme hatası: {str(replace_error)}")
                        # Hata olsa bile devam et
            
            # Slaytı PNG olarak export et (resolution: 1920x1080)
            image_path = os.path.join(output_dir, f'slide_{slide_idx:03d}.png')
            try:
                slide.Export(image_path, 'PNG', 1920, 1080)
                image_paths.append(image_path)
                print(f"✓ Slayt {slide_idx} görsel olarak export edildi")
            except Exception as export_error:
                print(f"✗ Slayt {slide_idx} export hatası: {str(export_error)}")
        
        # Kapat
        presentation.Close()
        powerpoint.Quit()
        
        # COM objelerini temizle
        del presentation
        del powerpoint
        
        return image_paths
        
    except Exception as e:
        raise Exception(f"Slayt export hatası: {str(e)}")


def create_slide_video(image_path: str, audio_path: Optional[str], duration: float) -> ImageClip:
    """
    Bir görsel ve ses dosyasından video klip oluşturur.
    
    Args:
        image_path: Görsel dosya yolu
        audio_path: Ses dosya yolu (opsiyonel)
        duration: Video süresi (saniye)
        
    Returns:
        VideoClip objesi
    """
    # Ses dosyası varsa gerçek süresini kullan, yoksa duration parametresini kullan
    actual_duration = duration
    if audio_path and os.path.exists(audio_path):
        try:
            audio = AudioFileClip(audio_path)
            actual_duration = audio.duration  # Gerçek ses süresini kullan
            audio.close()
        except Exception as e:
            print(f"Ses dosyası okunamadı, duration parametresi kullanılıyor: {str(e)}")
    
    # Görselden video klip oluştur - gerçek ses süresi kadar
    video = ImageClip(image_path)
    video = video.set_duration(actual_duration)  # Gerçek süreyi kullan
    video = video.set_fps(24)
    video = video.resize(newsize=(1920, 1080))  # Full HD
    
    # Ses dosyasını ekle
    if audio_path and os.path.exists(audio_path):
        try:
            audio = AudioFileClip(audio_path)
            video = video.set_audio(audio)
        except Exception as e:
            print(f"Ses eklenirken hata: {str(e)}, sadece görsel kullanılıyor")
    
    return video


def _fit_text_to_box(draw: ImageDraw.ImageDraw, text: str, font_path: Optional[str], box_width: int, box_height: int) -> ImageFont.FreeTypeFont:
    """
    Verilen kutu boyutlarına sığacak şekilde font boyutunu ayarlar ve font döner.
    """
    # Başlangıç font boyutu tahmini (ekran yüksekliğine göre makul bir değer)
    font_size = 48
    # Fallback font yüklenmesi için yardımcı
    def load_font(size: int):
        try:
            if font_path:
                return ImageFont.truetype(font_path, size=size)
            # Yaygın font isimleri deneyelim
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

    # Metni sarmak için bir fonksiyon
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

    # Font boyutunu düşürerek kutuya sığdırma
    for size in range(font_size, 12, -2):
        font = load_font(size)
        wrapped = wrap_text(text, font, box_width)
        w, h = draw.multiline_textsize(wrapped, font=font, spacing=8)
        if w <= box_width and h <= box_height:
            return font
    return load_font(12)


def create_overlay_image(base_image_path: str, text: str, output_path: str) -> str:
    """
    Slayt görselinin alt kısmına çevrilmiş metni okunaklı şekilde bindirir.
    """
    image = Image.open(base_image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    img_w, img_h = image.size

    # Metin kutusu boyutları (alt bölüm)
    margin = int(img_w * 0.05)
    box_width = img_w - 2 * margin
    box_height = int(img_h * 0.28)
    box_left = margin
    box_top = img_h - margin - box_height
    box_right = box_left + box_width
    box_bottom = box_top + box_height

    # Kutu arka planı (yarı saydam siyah)
    overlay_color = (0, 0, 0, 180)
    # Yarı saydam çizim için ayrı katman
    overlay = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([box_left, box_top, box_right, box_bottom], fill=overlay_color)
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)

    # Font ayarı ve metin sarma
    font = _fit_text_to_box(draw, text, font_path=None, box_width=box_width - margin, box_height=box_height - margin)

    # Metni yeniden wrap et ve ölç
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

    # Metni kutu içinde ortala (yatay), üstten biraz boşlukla
    text_x = box_left + (box_width - text_w) // 2
    text_y = box_top + (box_height - text_h) // 2

    # Metin rengi: beyaz
    draw.multiline_text((text_x, text_y), wrapped_text, font=font, fill=(255, 255, 255), spacing=8, align="center")

    image.save(output_path)
    return output_path

def create_video_from_json(json_file_path: str, pptx_file_path: str, progress_callback=None) -> str:
    """
    JSON dosyasındaki bilgileri kullanarak final video oluşturur.
    
    Args:
        json_file_path: Audio bilgileri içeren JSON dosyası
        pptx_file_path: Orijinal PowerPoint dosyası
        progress_callback: İlerleme callback fonksiyonu
        
    Returns:
        Oluşturulan video dosyasının yolu
    """
    # JSON dosyasını oku
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    slides = data.get('slides', [])
    total_slides = len(slides)
    
    # Çalışma klasörlerini oluştur
    json_dir = os.path.dirname(os.path.abspath(json_file_path))
    json_basename = os.path.splitext(os.path.basename(json_file_path))[0]
    images_dir = os.path.join(json_dir, f'{json_basename}_images')
    
    # Slayt görsellerini export et (çevrilmiş metinlerle birlikte)
    if progress_callback:
        progress_callback('PowerPoint slaytları görsele dönüştürülüyor (metinler çevriliyor)...')
    
    # slides bilgilerini export fonksiyonuna gönder
    image_paths = export_slides_to_images(pptx_file_path, images_dir, progress_callback, slides_data=slides)
    
    # Her slayt için video klip oluştur
    video_clips = []
    for idx, slide in enumerate(slides, 1):
        slide_number = slide.get('slide_number', idx)
        audio_file = slide.get('audio_file')
        duration = slide.get('duration', 5.0)  # Varsayılan 5 saniye
        
        if progress_callback:
            progress_callback(f'Video oluşturuluyor: Slayt {idx}/{total_slides}')
        
        # Görsel dosyasını bul
        image_path = os.path.join(images_dir, f'slide_{slide_number:03d}.png')
        
        # Eğer görsel yoksa, ilk görseli kullan veya atla
        if not os.path.exists(image_path) and image_paths:
            image_path = image_paths[slide_number - 1] if slide_number <= len(image_paths) else image_paths[0]
        
        if os.path.exists(image_path):
            # Çevrilmiş metni görsele bindir
            translated_text = slide.get('translated_text', '') or ''
            overlay_image_path = image_path
            if translated_text.strip():
                overlay_image_path = os.path.join(images_dir, f'slide_{slide_number:03d}_overlay.png')
                try:
                    create_overlay_image(image_path, translated_text, overlay_image_path)
                except Exception as e:
                    print(f"Overlay oluşturulamadı, orijinal görsel kullanılacak: {str(e)}")
                    overlay_image_path = image_path

            clip = create_slide_video(overlay_image_path, audio_file, duration)
            video_clips.append(clip)
            print(f"✓ Slayt {slide_number} video klibi oluşturuldu")
        else:
            print(f"⚠ Slayt {slide_number} görseli bulunamadı, atlanıyor")
    
    if not video_clips:
        raise Exception("Hiç video klip oluşturulamadı!")
    
    # Tüm klipleri birleştir
    if progress_callback:
        progress_callback('Video klipleri birleştiriliyor...')
    
    print(f"{len(video_clips)} video klip birleştiriliyor...")
    final_video = concatenate_videoclips(video_clips, method="compose")
    
    # Video dosyasını kaydet
    output_video_path = json_file_path.replace('.json', '').replace('_with_audio', '') + '_video.mp4'
    
    if progress_callback:
        progress_callback(f'Video kaydediliyor: {os.path.basename(output_video_path)}...')
    
    final_video.write_videofile(
        output_video_path,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=4
    )
    
    # Klipleri temizle
    for clip in video_clips:
        clip.close()
    final_video.close()
    
    print(f"✓ Video oluşturuldu: {output_video_path}")
    return output_video_path

