from pptx import Presentation
from typing import List, Dict


def extract_text_from_pptx(file_path: str) -> List[Dict]:
    """
    PowerPoint dosyasından her slayttaki metinleri çıkarır.
    
    Args:
        file_path: PowerPoint dosyasının yolu
        
    Returns:
        Her slayt için dict içeren liste. Her dict:
        {
            'slide_number': int,
            'text': str (birleştirilmiş tüm metin),
            'text_blocks': List[str] (paragraf paragraf metinler)
        }
    """
    try:
        prs = Presentation(file_path)
        slides_data = []
        
        for slide_num, slide in enumerate(prs.slides, start=1):
            text_blocks = []
            all_text = []
            
            # Her shape'i kontrol et (textbox, placeholder vb.)
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text_content = shape.text.strip()
                    text_blocks.append(text_content)
                    all_text.append(text_content)
            
            # Metin varsa slayt verisine ekle
            if all_text:
                slides_data.append({
                    'slide_number': slide_num,
                    'text': '\n'.join(all_text),
                    'text_blocks': text_blocks
                })
            else:
                # Metin yoksa boş slayt olarak ekle
                slides_data.append({
                    'slide_number': slide_num,
                    'text': '',
                    'text_blocks': []
                })
        
        return slides_data
    
    except Exception as e:
        raise Exception(f"PowerPoint dosyası okunurken hata oluştu: {str(e)}")


def get_slide_count(file_path: str) -> int:
    """
    PowerPoint dosyasındaki toplam slayt sayısını döndürür.
    """
    try:
        prs = Presentation(file_path)
        return len(prs.slides)
    except Exception as e:
        raise Exception(f"PowerPoint dosyası okunurken hata oluştu: {str(e)}")
