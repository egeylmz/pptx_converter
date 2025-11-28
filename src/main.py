import sys
import os
import json
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QFileDialog, QLabel, QComboBox)
from PyQt5.QtCore import Qt
from pptx_reader import extract_text_from_pptx, get_slide_count
from ppt_converter import convert_ppt_to_pptx, is_ppt_file
from tts_generator import generate_audio_for_json
from video_generator import create_video_from_json

TRANSLATOR_AVAILABLE = False
try:
    from translator import translate_texts
    TRANSLATOR_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    TRANSLATOR_AVAILABLE = False
    def translate_texts(*args, **kwargs):
        raise Exception("Çeviri özelliği Python 3.14 ile uyumlu değil. Python 3.11 veya 3.12 kullanmanız gerekiyor.")


class PPTXConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.converted_pptx_file = None  # Geçici dönüştürülen .pptx dosyası
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('PowerPoint Video Converter')
        self.setGeometry(100, 100, 1200, 600)
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Başlık
        title_label = QLabel('PowerPoint Video Converter')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 40px; font-weight: bold; margin: 40px;")
        layout.addWidget(title_label)
        
        # Dosya seçimi bölümü
        file_label = QLabel('Seçili dosya: Dosya seçilmedi')
        file_label.setWordWrap(True)
        file_label.setStyleSheet("padding: 20px; border: 2px solid #ccc; margin: 20px; font-size: 18px;")
        layout.addWidget(file_label)
        self.file_label = file_label
        
        select_file_btn = QPushButton('PowerPoint Dosyası Seç')
        select_file_btn.setStyleSheet("padding: 20px; font-size: 28px;")
        select_file_btn.clicked.connect(self.select_file)
        layout.addWidget(select_file_btn)
        
        # Dil seçimi bölümü
        lang_label = QLabel('Hedef Dil:')
        lang_label.setStyleSheet("font-size: 28px; margin-top: 40px;")
        layout.addWidget(lang_label)
        
        lang_combo = QComboBox()
        lang_combo.addItems([
            'İngilizce (en)',
            'Türkçe (tr)',
            'Almanca (de)',
            'Fransızca (fr)',
            'İspanyolca (es)',
            'İtalyanca (it)',
            'Rusça (ru)',
            'Japonca (ja)',
            'Korece (ko)',
            'Çince (zh)'
        ])
        lang_combo.setStyleSheet("padding: 16px; font-size: 28px;")
        layout.addWidget(lang_combo)
        self.lang_combo = lang_combo
        
        # İşleme butonu
        process_btn = QPushButton('Dönüştürmeyi Başlat')
        process_btn.setStyleSheet("padding: 24px; font-size: 32px; font-weight: bold; background-color: #4CAF50; color: white; margin-top: 40px;")
        process_btn.clicked.connect(self.start_conversion)
        layout.addWidget(process_btn)
        
        # Alt boşluk
        layout.addStretch()
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'PowerPoint Dosyası Seç',
            '',
            'PowerPoint Dosyaları (*.pptx);;Tüm Dosyalar (*)'
        )
        if file_path:
            # Windows yol formatını normalize et
            file_path = os.path.normpath(file_path)
            
            # .ppt dosyasıysa .pptx'e dönüştür
            converted_file = None
            if is_ppt_file(file_path):
                try:
                    self.file_label.setText('.ppt dosyası .pptx formatına dönüştürülüyor...\nLütfen bekleyin.')
                    self.file_label.setStyleSheet("padding: 20px; border: 2px solid #ff9800; margin: 20px; background-color: #fff3e0; font-size: 18px;")
                    
                    # GUI'yi güncellemek için
                    QApplication.processEvents()
                    
                    converted_file = convert_ppt_to_pptx(file_path)
                    file_path = converted_file  # Dönüştürülen dosyayı kullan
                    self.file_label.setText('.ppt dosyası başarıyla dönüştürüldü!')
                except Exception as e:
                    error_msg = (
                        f'.ppt dosyası dönüştürülemedi!\n\n'
                        f'Hata: {str(e)}\n\n'
                        'Lütfen:\n'
                        '1. PowerPoint\'in yüklü olduğundan emin olun\n'
                        '2. veya dosyayı manuel olarak .pptx\'e dönüştürün'
                    )
                    self.file_label.setText(error_msg)
                    self.file_label.setStyleSheet("padding: 20px; border: 2px solid #f44336; margin: 20px; background-color: #ffebee; font-size: 18px;")
                    return
            
            # Dosyanın var olup olmadığını kontrol et
            if not os.path.exists(file_path):
                self.file_label.setText(f'Hata: Dosya bulunamadı:\n{file_path}')
                self.file_label.setStyleSheet("padding: 10px; border: 1px solid #f44336; margin: 10px; background-color: #ffebee;")
                return
            
            try:
                slide_count = get_slide_count(file_path)
                self.selected_file = file_path  # Dönüştürülmüş veya orijinal dosya yolunu kullan
                # Orijinal dosya adını göster (eğer dönüştürüldüyse)
                original_file = os.path.basename(file_path) if converted_file is None else os.path.basename(converted_file).replace('converted_', '').replace('.pptx', '.ppt')
                status_text = f'Seçili dosya: {original_file}\nToplam {slide_count} slayt bulundu.'
                if converted_file:
                    status_text += '\n(Geçici olarak .pptx formatına dönüştürüldü)'
                self.file_label.setText(status_text)
                self.file_label.setStyleSheet("padding: 20px; border: 2px solid #4CAF50; margin: 20px; background-color: #e8f5e9; font-size: 18px;")
                
                # Dönüştürülen dosyayı sakla (sonra silmek için)
                if converted_file:
                    self.converted_pptx_file = converted_file
            except Exception as e:
                error_msg = str(e)
                # Daha kullanıcı dostu hata mesajı
                if 'Package not found' in error_msg or '.ppt' in file_path.lower():
                    error_msg = (
                        'PowerPoint dosyası açılamadı!\n\n'
                        'Olası nedenler:\n'
                        '• Dosya .ppt formatında (sadece .pptx desteklenir)\n'
                        '• Dosya bozuk veya korumalı\n'
                        '• Dosya başka bir program tarafından açık'
                    )
                else:
                    error_msg = f'Hata: {error_msg}'
                
                self.file_label.setText(error_msg)
                self.file_label.setStyleSheet("padding: 20px; border: 2px solid #f44336; margin: 20px; background-color: #ffebee; font-size: 18px;")
                print(f"Detaylı hata: {e}")
                import traceback
                traceback.print_exc()
    
    def update_translation_progress(self, message: str):
        """Çeviri ilerlemesini güncelle"""
        self.file_label.setText(message)
        QApplication.processEvents()  # UI'ı anında güncelle
    
    def start_conversion(self):
        if not self.selected_file:
            self.file_label.setText('Lütfen önce bir dosya seçin!')
            self.file_label.setStyleSheet("padding: 20px; border: 2px solid #f44336; margin: 20px; background-color: #ffebee; font-size: 18px;")
            return
        
        selected_lang = self.lang_combo.currentText()
        lang_code = selected_lang.split('(')[1].split(')')[0]
        
        try:
            # PowerPoint dosyasından metinleri çıkar
            print(f'Dosya: {self.selected_file}')
            print(f'Dil: {lang_code}')
            print('PowerPoint dosyası okunuyor...')
            slides_data = extract_text_from_pptx(self.selected_file)
            print(f'{len(slides_data)} slayt okundu.')
            
            # Metinleri çevir
            if not TRANSLATOR_AVAILABLE:
                self.file_label.setText('Uyarı: Çeviri modülü kullanılamıyor. Sadece okuma yapılıyor.')
                self.file_label.setStyleSheet("padding: 20px; border: 2px solid #ff9800; margin: 20px; background-color: #fff3e0; font-size: 18px;")
                translated_slides = slides_data
            else:
                print(f'Metinler {lang_code} diline çevriliyor...')
                self.file_label.setText('Metinler çevriliyor... Lütfen bekleyin.')
                QApplication.processEvents()  # UI'ı güncelle
                translated_slides = translate_texts(slides_data, lang_code, progress_callback=lambda msg: self.update_translation_progress(msg))
                print(f'{len(translated_slides)} slayt çevrildi.')
            
            # Çevrilen verileri JSON dosyasına kaydet
            output_data = {
                "source_file": os.path.basename(self.selected_file),
                "target_language": lang_code,
                "translation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_slides": len(translated_slides),
                "slides": [
                    {
                        "slide_number": slide.get("slide_number"),
                        "original_text": slide.get("text", ""),
                        "translated_text": slide.get("translated_text", ""),
                        "original_blocks": slide.get("text_blocks", []),
                        "translated_blocks": slide.get("translated_blocks", []),
                        "audio_file": None,  # TTS'den sonra buraya eklenecek
                        "duration": None  # Ses dosyası süresi
                    }
                    for slide in translated_slides
                ]
            }
            
            # output klasörünü oluştur (yoksa)
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
            os.makedirs(output_dir, exist_ok=True)
            
            # JSON dosya adını oluştur
            source_filename = os.path.splitext(os.path.basename(self.selected_file))[0]
            json_filename = f"{source_filename}_{lang_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_filepath = os.path.join(output_dir, json_filename)
            
            # JSON dosyasına kaydet
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f'Çevrilen veriler kaydedildi: {json_filepath}')
            
            # TTS işlemini başlat
            self.file_label.setText('Ses dosyaları oluşturuluyor... Lütfen bekleyin.')
            QApplication.processEvents()
            try:
                audio_json_path = generate_audio_for_json(
                    json_filepath, 
                    progress_callback=lambda msg: self.update_translation_progress(msg)
                )
                print(f'Audio JSON kaydedildi: {audio_json_path}')
                
                # Video oluşturmayı başlat
                self.file_label.setText('Video oluşturuluyor... Bu işlem uzun sürebilir. Lütfen bekleyin.')
                QApplication.processEvents()
                
                try:
                    video_path = create_video_from_json(
                        audio_json_path,
                        self.selected_file,
                        progress_callback=lambda msg: self.update_translation_progress(msg)
                    )
                    print(f'Video oluşturuldu: {video_path}')
                    
                    success_msg = (
                        f'✓ TÜM İŞLEMLER TAMAMLANDI!\n\n'
                        f'{len(translated_slides)} slayt çevrildi, ses dosyaları ve video oluşturuldu.\n\n'
                        f'JSON: {os.path.basename(json_filepath)}\n'
                        f'Audio JSON: {os.path.basename(audio_json_path)}\n'
                        f'Video: {os.path.basename(video_path)}'
                    )
                    self.file_label.setText(success_msg)
                    self.file_label.setStyleSheet("padding: 20px; border: 2px solid #4CAF50; margin: 20px; background-color: #e8f5e9; font-size: 18px;")
                except Exception as video_error:
                    print(f'Video hatası: {video_error}')
                    import traceback
                    traceback.print_exc()
                    # Video hatası olsa bile TTS başarılı mesajı göster
                    success_msg = (
                        f'✓ Çeviri ve TTS tamamlandı!\n\n'
                        f'{len(translated_slides)} slayt çevrildi ve ses dosyaları oluşturuldu.\n\n'
                        f'Video hatası: {str(video_error)}\n\n'
                        f'JSON: {os.path.basename(json_filepath)}\n'
                        f'Audio JSON: {os.path.basename(audio_json_path)}'
                    )
                    self.file_label.setText(success_msg)
                    self.file_label.setStyleSheet("padding: 20px; border: 2px solid #ff9800; margin: 20px; background-color: #fff3e0; font-size: 18px;")
            except Exception as tts_error:
                print(f'TTS hatası: {tts_error}')
                import traceback
                traceback.print_exc()
                # TTS hatası olsa bile çeviri başarılı mesajı göster
                success_msg = (
                    f'Çeviri tamamlandı! {len(translated_slides)} slayt çevrildi.\n\n'
                    f'TTS hatası: {str(tts_error)}\n\n'
                    f'Kayıt yeri: {json_filename}'
                )
                self.file_label.setText(success_msg)
                self.file_label.setStyleSheet("padding: 20px; border: 2px solid #ff9800; margin: 20px; background-color: #fff3e0; font-size: 18px;")
        except Exception as e:
            self.file_label.setText(f'Dönüştürme hatası: {str(e)}')
            self.file_label.setStyleSheet("padding: 20px; border: 2px solid #f44336; margin: 20px; background-color: #ffebee; font-size: 18px;")


def main():
    app = QApplication(sys.argv)
    window = PPTXConverterApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

