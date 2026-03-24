# ─────────────────────────────────────────────────────────────────────────────
# chromadb_cleanup.py — ChromaDB Management Utility
#
# PURPOSE: Help manage ChromaDB collections and clear stale data
#          When PDFs are deleted, their embeddings may persist in ChromaDB
#          This utility helps clear and rebuild collections
#
# ─────────────────────────────────────────────────────────────────────────────

import os
import shutil
from pathlib import Path

CHROMA_STORE_PATH = "./chroma_store"


def get_chromadb_status() -> dict:
    """
    Get status of ChromaDB collections.
    Returns info about what data is stored.
    """
    status = {
        "chroma_exists": os.path.exists(CHROMA_STORE_PATH),
        "chroma_size_mb": 0,
        "collections": []
    }
    
    if status["chroma_exists"]:
        # Calculate size
        total_size = 0
        for path, dirs, files in os.walk(CHROMA_STORE_PATH):
            for file in files:
                filepath = os.path.join(path, file)
                total_size += os.path.getsize(filepath)
        status["chroma_size_mb"] = round(total_size / (1024 * 1024), 2)
        
        # List subdirectories (collection UUIDs)
        if os.path.isdir(CHROMA_STORE_PATH):
            items = os.listdir(CHROMA_STORE_PATH)
            status["collections"] = [item for item in items if os.path.isdir(os.path.join(CHROMA_STORE_PATH, item))]
    
    return status


def clear_chromadb() -> bool:
    """
    ⚠️ DANGER: Completely clear ChromaDB storage.
    This removes ALL collected documents and their embeddings.
    
    Use this if stale PDF data is causing issues.
    You'll need to re-upload and rebuild collections afterward.
    
    Returns: True if cleared successfully, False otherwise
    """
    if not os.path.exists(CHROMA_STORE_PATH):
        print("[ChromaDB] No chroma_store folder found. Nothing to clear.")
        return True
    
    try:
        shutil.rmtree(CHROMA_STORE_PATH)
        print(f"[ChromaDB] ✅ Cleared entire ChromaDB database at {CHROMA_STORE_PATH}")
        return True
    except Exception as e:
        print(f"[ChromaDB] ❌ Error clearing ChromaDB: {str(e)}")
        return False


def print_chromadb_info():
    """
    Print current ChromaDB status to console.
    """
    status = get_chromadb_status()
    
    print("\n" + "="*60)
    print("ChromaDB Status Report")
    print("="*60)
    
    if status["chroma_exists"]:
        print(f"✅ ChromaDB Store Exists: {CHROMA_STORE_PATH}")
        print(f"📊 Total Size: {status['chroma_size_mb']} MB")
        print(f"📦 Stored Collections: {len(status['collections'])}")
        if status['collections']:
            print("\n   Collection UUIDs (internal storage):")
            for col in status['collections']:
                col_path = os.path.join(CHROMA_STORE_PATH, col)
                col_size = 0
                for path, dirs, files in os.walk(col_path):
                    for file in files:
                        col_size += os.path.getsize(os.path.join(path, file))
                print(f"   - {col} ({round(col_size / 1024, 2)} KB)")
    else:
        print(f"❌ ChromaDB Store Does NOT Exist")
        print(f"   Path: {CHROMA_STORE_PATH}")
        print("   (Collections will be created on first document upload)")
    
    print("\n⚠️  If agents are using stale/old PDF data:")
    print("   1. Call: clear_chromadb()")
    print("   2. The system will rebuild collections on next upload")
    print("   3. Upload new documents via the Streamlit app")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Show current status
    print_chromadb_info()
    
    # Ask user if they want to clear
    response = input("Do you want to CLEAR the ChromaDB to remove stale data? (yes/no): ").strip().lower()
    if response == "yes":
        if clear_chromadb():
            print("✅ ChromaDB cleared successfully!")
            print("   Please re-upload your documents through the Streamlit app.")
        else:
            print("❌ Failed to clear ChromaDB. Check file permissions.")
    else:
        print("Cancelled. ChromaDB unchanged.")
