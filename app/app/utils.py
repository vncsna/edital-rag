from pathlib import Path

from pypdf import PdfReader


def get_pdf_as_txt(filepath: Path) -> str:
    filepath_txt = filepath.with_suffix(".txt")

    if filepath_txt.exists():
        return filepath_txt.read_text()

    reader = PdfReader(filepath)

    text = ""
    for page in reader.pages:
        text += page.extract_text()

    filepath_txt.write_text(text)

    return text
