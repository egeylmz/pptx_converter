from typing import List, Dict
import time

# deep-translator kullan (Python 3.14 uyumlu)
try:
    from deep_translator import GoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False
    # Fallback olarak googletrans'ı dene
    try:
        from googletrans import Translator
        GOOGLETRANS_AVAILABLE = True
    except:
        GOOGLETRANS_AVAILABLE = False


def translate_texts(slides_data: List[Dict], target_lang: str, progress_callback=None) -> List[Dict]:
    """
    Slayt metinlerini hedef dile çevirir.
    
    Args:
        slides_data: extract_text_from_pptx() fonksiyonundan dönen liste
        target_lang: Hedef dil kodu (örn: 'en', 'tr', 'de')
        
    Returns:
        Çevrilmiş metinleri içeren aynı formatta liste. Her dict'e 'translated_text' eklenir.
    """
    # Çeviri motorunu seç
    if DEEP_TRANSLATOR_AVAILABLE:
        translator = GoogleTranslator(source='auto', target=target_lang)
        translate_func = lambda text: translator.translate(text)
    elif GOOGLETRANS_AVAILABLE:
        translator = Translator()
        translate_func = lambda text: translator.translate(text, dest=target_lang).text
    else:
        raise Exception("Hiçbir çeviri modülü bulunamadı. 'deep-translator' veya 'googletrans' kurulu olmalı.")
    
    translated_slides = []
    total_slides = len(slides_data)
    
    for slide in slides_data:
        try:
            if slide['text'].strip():
                # Metni çevir (retry mekanizması ile)
                max_retries = 3
                translated_text = None
                for attempt in range(max_retries):
                    try:
                        status_msg = f'Çevriliyor: Slayt {slide['slide_number']}/{total_slides} (deneme {attempt + 1}/{max_retries})'
                        print(f"Slayt {slide['slide_number']} çevriliyor... (deneme {attempt + 1}/{max_retries})")
                        if progress_callback:
                            progress_callback(status_msg)
                        translated_text = translate_func(slide['text'])
                        print(f"✓ Slayt {slide['slide_number']} başarıyla çevrildi")
                        if progress_callback:
                            progress_callback(f'✓ Slayt {slide['slide_number']}/{total_slides} tamamlandı')
                        break  # Başarılı olursa döngüden çık
                    except Exception as retry_error:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # 2, 4, 6 saniye bekle
                            print(f"✗ Slayt {slide['slide_number']} çeviri denemesi {attempt + 1}/{max_retries} başarısız. {wait_time}s bekleniyor... Hata: {str(retry_error)}")
                            time.sleep(wait_time)
                        else:
                            print(f"✗✗ Slayt {slide['slide_number']} tüm çeviri denemeleri başarısız!")
                            raise retry_error  # Son denemede hata varsa yukarı fırlat
                
                if translated_text is None or not translated_text.strip():
                    raise Exception("Çeviri sonucu boş veya None döndü")
                
                # Çevrilmiş metni de paragraflara böl (orijinal yapıyı koru)
                translated_blocks = []
                if slide.get('text_blocks'):
                    for block_idx, block in enumerate(slide['text_blocks']):
                        if block.strip():
                            # Her block için de retry yap
                            block_translated = None
                            for attempt in range(max_retries):
                                try:
                                    block_translated = translate_func(block)
                                    break
                                except Exception as retry_error:
                                    if attempt < max_retries - 1:
                                        time.sleep((attempt + 1) * 1)  # Bloklar için daha kısa bekleme
                                    else:
                                        print(f"Block {block_idx + 1} çevrilemedi: {str(retry_error)}")
                                        raise retry_error
                            translated_blocks.append(block_translated if block_translated else '')
                        else:
                            translated_blocks.append('')
                
                translated_slide = slide.copy()
                translated_slide['translated_text'] = translated_text
                translated_slide['translated_blocks'] = translated_blocks
                translated_slides.append(translated_slide)
                
                print(f"Slayt {slide['slide_number']} çevrildi: {translated_text[:50]}...")
                
                # Rate limiting için kısa bekleme
                time.sleep(0.5)  # Rate limiting için bekleme süresini artırdık
                if progress_callback:
                    progress_callback(f'Slayt {slide['slide_number']}/{total_slides} işlendi')
            else:
                # Boş slayt
                translated_slide = slide.copy()
                translated_slide['translated_text'] = ''
                translated_slide['translated_blocks'] = []
                translated_slides.append(translated_slide)
                
        except Exception as e:
            import traceback
            error_msg = f"Slayt {slide['slide_number']} çevrilirken hata: {str(e)}"
            print(error_msg)
            print(f"Detaylı hata: {traceback.format_exc()}")
            # Hata durumunda boş çeviri ile kaydet (çeviri yapılamadığını belirtmek için)
            translated_slide = slide.copy()
            translated_slide['translated_text'] = ''  # Çeviri yapılamadı
            translated_slide['translated_blocks'] = []
            translated_slide['translation_error'] = str(e)  # Hata mesajını da ekle
            translated_slides.append(translated_slide)
    
    return translated_slides


def translate_single_text(text: str, target_lang: str) -> str:
    """
    Tek bir metin parçasını çevirir.
    
    Args:
        text: Çevrilecek metin
        target_lang: Hedef dil kodu
        
    Returns:
        Çevrilmiş metin
    """
    try:
        if DEEP_TRANSLATOR_AVAILABLE:
            translator = GoogleTranslator(source='auto', target=target_lang)
            return translator.translate(text)
        elif GOOGLETRANS_AVAILABLE:
            translator = Translator()
            return translator.translate(text, dest=target_lang).text
        else:
            raise Exception("Hiçbir çeviri modülü bulunamadı")
    except Exception as e:
        print(f"Çeviri hatası: {str(e)}")
        return text

