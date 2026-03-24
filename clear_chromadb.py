# ─────────────────────────────────────────────────────────────────────────────
# clear_chromadb.py — ChromaDB Management Script
#
# PURPOSE: Help manage ChromaDB and clear stale PDF embeddings
#          When PDFs are deleted, their embeddings persist in ChromaDB
#          This script helps clear the database completely
#
# USAGE:
#   python clear_chromadb.py
#
# ─────────────────────────────────────────────────────────────────────────────

import os
import shutil
from pathlib import Path

CHROMA_STORE_PATH = "./chroma_store"


def get_chromadb_status():
    """Get status of ChromaDB storage."""
    status = {
        "exists": os.path.exists(CHROMA_STORE_PATH),
        "size_mb": 0,
        "collections": []
    }
    
    if status["exists"]:
        # Calculate size
        total_size = 0
        for path, dirs, files in os.walk(CHROMA_STORE_PATH):
            for file in files:
                filepath = os.path.join(path, file)
                total_size += os.path.getsize(filepath)
        status["size_mb"] = round(total_size / (1024 * 1024), 2)
        
        # List stored collections
        if os.path.isdir(CHROMA_STORE_PATH):
            items = os.listdir(CHROMA_STORE_PATH)
            status["collections"] = len([item for item in items if os.path.isdir(os.path.join(CHROMA_STORE_PATH, item)) and item != "__pycache__"])
    
    return status


def clear_chromadb():
    """Completely clear ChromaDB storage to remove stale data."""
    if not os.path.exists(CHROMA_STORE_PATH):
        print("✅ No stale ChromaDB found. Nothing to clear.")
        return True
    
    try:
        shutil.rmtree(CHROMA_STORE_PATH)
        print(f"✅ ChromaDB cleared successfully!")
        print(f"   Deleted: {CHROMA_STORE_PATH}")
        return True
    except Exception as e:
        print(f"❌ Error clearing ChromaDB: {str(e)}")
        return False


def print_status():
    """Print ChromaDB status."""
    status = get_chromadb_status()
    
    print("\n" + "="*70)
    print("ChromaDB Status Report")
    print("="*70)
    
    if status["exists"]:
        print(f"📊 Status: ✅ ChromaDB Store Found")
        print(f"   Location: {CHROMA_STORE_PATH}")
        print(f"   Size: {status['size_mb']} MB")
        print(f"   Collections: {status['collections']}")
        print("\n⚠️  This database contains ALL old PDF embeddings.")
        print("   If agents are using outdated PDF data, you should clear this.")
    else:
        print(f"📊 Status: ❌ ChromaDB Store Not Found")
        print(f"   Agents will create new collections on first upload")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    print_status()
    
    response = input("🔴 CLEAR ChromaDB and remove all stale PDF data? (yes/no): ").strip().lower()
    if response in ["yes", "y"]:
        if clear_chromadb():
            print("\n✅ Done! ChromaDB is now empty.")
            print("📝 Instructions:")
            print("   1. Restart the Streamlit app")
            print("   2. Upload ONLY the CSV files you want to use")
            print("   3. Agents will now work with fresh data only")
        else:
            print("\n❌ Failed to clear ChromaDB")
    else:
        print("\n⏭️  Cancelled. ChromaDB unchanged.")
