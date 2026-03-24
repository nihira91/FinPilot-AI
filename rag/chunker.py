
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
   
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""]  
    )
    return splitter.split_text(text)


def chunk_documents(documents: dict) -> list:
   
    all_chunks = []

    for filename, text in documents.items():
        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text":     chunk,
                "source":   filename,
                # chunk_id must be a UNIQUE string
                "chunk_id": f"{filename}_chunk_{i}"
            })

    print(f"[chunker] Total chunks created: {len(all_chunks)}")
    return all_chunks