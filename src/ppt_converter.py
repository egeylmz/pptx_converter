import os
import tempfile
from pathlib import Path


def convert_ppt_to_pptx(ppt_file_path: str) -> str:
    """
    Converts a .ppt file to .pptx on Windows.
    Uses PowerPoint's Windows COM interface.

    Args:
        ppt_file_path: Path to the .ppt file

    Returns:
        Path to the created .pptx file

    Raises:
        Exception: If conversion fails
    """
    try:
        import win32com.client
    except ImportError:
        raise Exception(
            "pywin32 is not installed for PPT conversion.\n"
            "To install: pip install pywin32"
        )

    # Create temporary .pptx file path
    ppt_path = Path(ppt_file_path)
    temp_dir = tempfile.gettempdir()
    pptx_file_path = os.path.join(temp_dir, f"converted_{ppt_path.stem}.pptx")

    try:
        # Start PowerPoint application
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        powerpoint.Visible = 1  # Visible mode (1) or hidden mode (0)

        # Open .ppt file
        presentation = powerpoint.Presentations.Open(os.path.abspath(ppt_file_path))

        # Save as .pptx
        presentation.SaveAs(os.path.abspath(pptx_file_path), 24)  # 24 = ppSaveAsOpenXMLPresentation (.pptx)

        # Close
        presentation.Close()
        powerpoint.Quit()

        # Clean up PowerPoint COM objects
        del presentation
        del powerpoint

        # Check if the file was created
        if os.path.exists(pptx_file_path):
            return pptx_file_path
        else:
            raise Exception("Converted file could not be created")

    except Exception as e:
        raise Exception(f"Error converting PPT to PPTX: {str(e)}")


def is_ppt_file(file_path: str) -> bool:
    """Checks if the file is in .ppt format."""
    return os.path.splitext(file_path)[1].lower() == '.ppt'