from gtts import gTTS
from typing import List, Dict
import os
import json
from pathlib import Path
import re


def get_language_code_for_tts(lang_code: str) -> str:
    """
    Çeviri dil kodunu gTTS dil koduna çevirir.
    
    Args:
        lang_code: Çeviri dil kodu (örn: 'en', 'tr', 'de')
        
    Returns:
        gTTS dil kodu
    """
    # gTTS dil kodları mapping
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
    return lang_map.get(lang_code, 'en')  # Varsayılan İngilizce


def generate_audio_for_text(text: str, lang_code: str, output_path: str) -> float:
    """
    Verilen metni TTS ile ses dosyasına çevirir.
    
    Args:
        text: Çevrilecek metin
        lang_code: Dil kodu (örn: 'en', 'tr')
        output_path: Çıktı dosya yolu (.mp3)
        
    Returns:
        Ses dosyasının süresi (saniye cinsinden)
    """
    if not text or not text.strip():
        # Boş metin için boş ses dosyası oluştur
        with open(output_path, 'wb') as f:
            f.write(b'')
        return 0.0
    
    try:
        tts_lang = get_language_code_for_tts(lang_code)
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        tts.save(output_path)
        
        # Ses dosyasının gerçek süresini oku (MoviePy kullanarak)
        try:
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(output_path)
            actual_duration = audio.duration
            audio.close()
            return actual_duration
        except Exception as e:
            print(f"Ses süresi okunamadı, tahmin kullanılıyor: {str(e)}")
            # Fallback: Ortalama konuşma hızı: ~150 kelime/dakika = ~2.5 kelime/saniye
            word_count = len(text.split())
            estimated_duration = word_count / 2.5
            return estimated_duration
    except Exception as e:
        print(f"TTS hatası: {str(e)}")
        # Hata durumunda boş dosya oluştur
        with open(output_path, 'wb') as f:
            f.write(b'')
        return 0.0


def generate_audio_for_json(json_file_path: str, progress_callback=None) -> str:
    """
    JSON dosyasındaki tüm slaytlar için TTS ses dosyaları oluşturur.
    
    Args:
        json_file_path: JSON dosyasının yolu
        progress_callback: İlerleme callback fonksiyonu (opsiyonel)
        
    Returns:
        Güncellenmiş JSON dosyasının yolu
    """
    # JSON dosyasını oku
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ses dosyaları için klasör oluştur
    json_dir = os.path.dirname(os.path.abspath(json_file_path))
    json_basename = os.path.splitext(os.path.basename(json_file_path))[0]
    audio_dir = os.path.join(json_dir, f'{json_basename}_audio')
    os.makedirs(audio_dir, exist_ok=True)
    
    target_lang = data.get('target_language', 'en')
    slides = data.get('slides', [])
    total_slides = len(slides)
    
    # Her slayt için ses dosyası oluştur
    for idx, slide in enumerate(slides, 1):
        slide_number = slide.get('slide_number', idx)
        translated_text = slide.get('translated_text', '')
        
        # Başta yalnızca rakamlardan oluşan slayt numarası satırını kaldır
        def strip_leading_slide_number(text: str) -> str:
            lines = text.splitlines()
            # Örn: "2", "12", "3.", "4)" gibi sadece numara/punct olan satırları baştan kaldır
            while lines and re.match(r'^\s*\d+\s*[\.)]?\s*$', lines[0]):
                lines.pop(0)
            return "\n".join(lines).lstrip()
        
        translated_text = strip_leading_slide_number(translated_text)
        
        if progress_callback:
            progress_callback(f'TTS: Slayt {idx}/{total_slides} işleniyor...')
        
        # Ses dosya adı
        audio_filename = f'slide_{slide_number:03d}.mp3'
        audio_path = os.path.join(audio_dir, audio_filename)
        
        # TTS ile ses dosyası oluştur
        duration = generate_audio_for_text(translated_text, target_lang, audio_path)
        
        # JSON'u güncelle
        slide['audio_file'] = audio_path
        slide['duration'] = round(duration, 2)
        
        print(f"✓ Slayt {slide_number} için ses dosyası oluşturuldu: {audio_filename} ({duration:.2f}s)")
    
    # Güncellenmiş JSON'u kaydet
    output_json_path = json_file_path.replace('.json', '_with_audio.json')
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    if progress_callback:
        progress_callback(f'TTS tamamlandı! {total_slides} slayt için ses dosyası oluşturuldu.')
    
    return output_json_path

