
#  Open PDF files and extract all their text as plain strings.


import os
from pypdf import PdfReader   # PdfReader opens a PDF and gives a list of Page objects


def load_pdf(file_path: str) -> str:
    """
    Open one PDF file and return ALL its pages joined into a single string.
    """
    reader = PdfReader(file_path)

    all_text = []
    for page in reader.pages:
        text = page.extract_text()   # pulls raw text from a single page
        if text:                     
            all_text.append(text)

    return "\n".join(all_text)


def load_all_pdfs(folder_path: str) -> dict:
    """
    Load every .pdf in a folder.

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
