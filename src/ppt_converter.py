import os
import tempfile
from pathlib import Path


def convert_ppt_to_pptx(ppt_file_path: str) -> str:
    """
    Windows'ta .ppt dosyasını .pptx'e dönüştürür.
    PowerPoint'in Windows COM interface'ini kullanır.
    
    Args:
        ppt_file_path: .ppt dosyasının yolu
        
    Returns:
        Oluşturulan .pptx dosyasının yolu
        
    Raises:
        Exception: Dönüştürme başarısız olursa
    """
    try:
        import win32com.client
    except ImportError:
        raise Exception(
            "PPT dönüştürme için pywin32 kurulu değil.\n"
            "Kurulum için: pip install pywin32"
        )
    
    # Geçici .pptx dosya yolu oluştur
    ppt_path = Path(ppt_file_path)
    temp_dir = tempfile.gettempdir()
    pptx_file_path = os.path.join(temp_dir, f"converted_{ppt_path.stem}.pptx")
    
    try:
        # PowerPoint uygulamasını başlat
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        powerpoint.Visible = 1  # Görünür mod (1) veya gizli mod (0)
        
        # .ppt dosyasını aç
        presentation = powerpoint.Presentations.Open(os.path.abspath(ppt_file_path))
        
        # .pptx olarak kaydet
        presentation.SaveAs(os.path.abspath(pptx_file_path), 24)  # 24 = ppSaveAsOpenXMLPresentation (.pptx)
        
        # Kapat
        presentation.Close()
        powerpoint.Quit()
        
        # PowerPoint COM objelerini temizle
        del presentation
        del powerpoint
        
        # Dosyanın oluşturulduğunu kontrol et
        if os.path.exists(pptx_file_path):
            return pptx_file_path
        else:
            raise Exception("Dönüştürülen dosya oluşturulamadı")
            
    except Exception as e:
        raise Exception(f"PPT'den PPTX'e dönüştürme hatası: {str(e)}")


def is_ppt_file(file_path: str) -> bool:
    """Dosyanın .ppt formatında olup olmadığını kontrol eder."""
    return os.path.splitext(file_path)[1].lower() == '.ppt'

