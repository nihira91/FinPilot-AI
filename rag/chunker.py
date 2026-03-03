# ─────────────────────────────────────────────────────────────────────────────
# chunker.py
#
# PURPOSE : Split long document text into smaller, overlapping pieces ("chunks").
#
# WHY DO WE CHUNK ?
#   An LLM has a context-window limit (e.g. 4 096 or 8 192 tokens).
#   A 40-page consultant report is far too long to pass in whole.
#   We break it into ~500-character pieces and only send the TOP-K most
#   relevant pieces to the LLM — this is the core idea of RAG.
#
# WHY OVERLAP ?
#   If a key sentence sits exactly at the border between two chunks,
#   overlap (shared characters between neighbours) ensures that sentence
#   is fully captured in at least one chunk and not cut in half.
#
# WHY RecursiveCharacterTextSplitter ?
#   It tries to split on paragraph breaks first (\n\n), then single newlines,
#   then spaces, then individual characters as a last resort.
#   This keeps chunks semantically meaningful rather than cutting mid-sentence.
# ─────────────────────────────────────────────────────────────────────────────

from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Split one text string into a list of smaller strings.

    Args:
        text       : the full document text (from pdf_loader)
        chunk_size : max characters per chunk  (500 chars ≈ 100 words)
        overlap    : characters shared between adjacent chunks

    Returns:
        List of strings — each string is one chunk.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""]   # try these in order when splitting
    )
    return splitter.split_text(text)


def chunk_documents(documents: dict) -> list:
    """
    Chunk every document and attach metadata to each chunk.

    Args:
        documents : { filename : full_text }  from load_all_pdfs()

    Returns:
        List of dicts:
        [
          { "text": "...", "source": "report.pdf", "chunk_id": "report.pdf_0" },
          ...
        ]

    WHY attach metadata ?
        ChromaDB stores metadata alongside each vector.
        When we retrieve a chunk, we also get back its source filename,
        so the agent can cite which document its answer came from.
    """
    all_chunks = []

    for filename, text in documents.items():
        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text":     chunk,
                "source":   filename,
                # chunk_id must be a UNIQUE string — ChromaDB uses it as a primary key
                "chunk_id": f"{filename}_chunk_{i}"
            })

    print(f"[chunker] Total chunks created: {len(all_chunks)}")
    return all_chunks