# Open PDF files and extract all their text as plain strings.

import os
from pypdf import PdfReader   # PdfReader opens a PDF and gives a list of Page objects


def load_pdf(file_path: str) -> str:
    """
    Open one PDF file and return ALL its pages joined into a single string.

    Args:
        file_path : full or relative path to the .pdf file

    Returns:
        One big string containing the text of every page.
    """
    reader = PdfReader(file_path)
    # reader.pages  →  list of Page objects, one per physical page in the PDF

    all_text = []
    for page in reader.pages:
        text = page.extract_text()   # pulls raw text from a single page
        if text:                     # some pages are image-only and return None
            all_text.append(text)

    # "\n".join(...) keeps page breaks readable as newlines
    return "\n".join(all_text)


def load_all_pdfs(folder_path: str) -> dict:
    """
    Load every .pdf in a folder.

    Args:
        folder_path : path to a folder that contains .pdf files

    Returns:
        { "report.pdf" : "full text …", "analysis.pdf" : "full text …" }
    """
    documents = {}

    if not os.path.exists(folder_path):
        print(f"[pdf_loader] Folder not found: {folder_path} — skipping.")
        return documents

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):        # skip .DS_Store, .txt, etc.
            full_path = os.path.join(folder_path, filename)
            print(f"[pdf_loader] Loading: {filename}")
            documents[filename] = load_pdf(full_path)

    print(f"[pdf_loader] Loaded {len(documents)} PDF(s) from {folder_path}")
    return documents
