from PyPDF2 import PdfReader

def parse_pdf(file_path: str) -> list[str]:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    lines = text.split("\n")
    return lines[:10]