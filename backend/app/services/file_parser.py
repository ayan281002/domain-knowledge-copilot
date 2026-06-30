from pathlib import Path

import docx
import markdown as markdown_lib
import pdfplumber


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}


def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")
    return ext


def parse_file(file_path: str) -> list[dict]:
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        pages: list[dict] = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                pages.append({"page_number": i, "text": page.extract_text() or ""})
        return pages

    if ext == ".docx":
        doc = docx.Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
        return [{"page_number": 1, "text": text}]

    if ext in {".txt", ".md", ".markdown"}:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        if ext in {".md", ".markdown"}:
            raw = markdown_lib.markdown(raw)
        return [{"page_number": 1, "text": raw}]

    raise ValueError("Unsupported file format")
