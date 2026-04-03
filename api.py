import os
import json
import shutil
import time
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from orchestrator.chatbot import process_chat_question
from rag.pipeline import build_collection

load_dotenv()

app = FastAPI(title="FinPilot AI Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_UPLOADS_ROOT = "temp_uploads"
os.makedirs(TEMP_UPLOADS_ROOT, exist_ok=True)

# Store user sessions and their uploaded documents
# Each session keeps track of uploaded files, data sheets, and analysis history
SESSION_STATE = {}

def get_session(session_id: str):
    if session_id not in SESSION_STATE:
        SESSION_STATE[session_id] = {
            "financial_csv": None,
            "sales_csv": None,
            "uploaded_collections": {}
        }
    return SESSION_STATE[session_id]

class ChatRequest(BaseModel):
    session_id: str
    query: str

class ClearRequest(BaseModel):
    session_id: str

@app.post("/api/upload")
async def upload_documents(
    session_id: str = Form(...),
    collection: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Upload your financial documents, reports, and data files for intelligent analysis.
    Your files are securely stored and ready to be analyzed by our specialist agents.
    """
    state = get_session(session_id)
    
    # Map React's 'financial' back to Python's 'financial_reports'
    collection_map = {
        "financial": "financial_reports",
        "sales": "sales_reports",
        "investment": "investment_reports",
        "cloud": "cloud_docs"
    }
    target_col = collection_map.get(collection, collection)
    
    temp_folder = os.path.join(TEMP_UPLOADS_ROOT, session_id, target_col)
    os.makedirs(temp_folder, exist_ok=True)
    
    if target_col not in state["uploaded_collections"]:
        state["uploaded_collections"][target_col] = []

    has_pdf = False

    for file in files:
        filename = file.filename
        content = await file.read()
        
        if filename.endswith(".csv"):
            import io
            df = pd.read_csv(io.BytesIO(content))
            if target_col == "financial_reports":
                state["financial_csv"] = df
            elif target_col == "sales_reports":
                state["sales_csv"] = df
            print(f"[API] Read CSV {filename} for {target_col}: {df.shape}")
        else:
            save_path = os.path.join(temp_folder, filename)
            with open(save_path, "wb") as f:
                f.write(content)
            has_pdf = True
            if filename not in state["uploaded_collections"][target_col]:
                state["uploaded_collections"][target_col].append(filename)
                
    if has_pdf:
        # Process and index your documents so they're ready for analysis
        try:
            print(f"[API] Building collection {target_col} for session {session_id}...")
            build_collection(target_col, session_id=session_id)
        except Exception as e:
            if "already exists" not in str(e).lower() and "ephemeral" not in str(e).lower():
                print(f"[API] Expected RAG warning/error: {e}")

    return {"status": "success", "uploaded": len(files)}

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Ask your intelligent assistant anything about your financial data.
    Get instant insights, recommendations, and analysis powered by AI specialists.
    """
    state = get_session(req.session_id)
    
    try:
        # Connect your query to the right specialist to answer your question
        result = process_chat_question(
            question=req.query,
            financial_csv=state.get("financial_csv"),
            sales_csv=state.get("sales_csv"),
            financial_column_mapping=None,  # let it auto-detect
            sales_column_mapping=None,      # let it auto-detect
            previous_agents=None, 
            uploaded_collections=state.get("uploaded_collections")
        )
        
        # Prepare charts and visualizations for your results
        vis_payload = None
        if result.get("visualization_data"):
            vis_payload = {}
            for agent, fig in result["visualization_data"].items():
                # Format visual insights for display
                try:
                    vis_payload[agent] = json.loads(fig.to_json())
                except Exception as e:
                    print(f"[API] Error serializing plotly fig for {agent}: {e}")
        
        return {
            "success": True,
            "final_answer": result.get("final_answer", ""),
            "agents_summary": result.get("agents_summary", ""),
            "agents": result.get("agents", []),
            "visualizations": vis_payload
        }
    except Exception as e:
        print(f"[API] Chat Error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/clear")
async def clear_session(req: ClearRequest):
    """
    Start fresh with a new analysis session.
    Remove all previous documents and start analyzing new data.
    """
    session_id = req.session_id
    if session_id in SESSION_STATE:
        del SESSION_STATE[session_id]
        
    session_temp_folder = os.path.join(TEMP_UPLOADS_ROOT, session_id)
    if os.path.exists(session_temp_folder):
        shutil.rmtree(session_temp_folder)
        
    # Clean up files from this session to free up space and reset state
    
    return {"status": "cleared"}

if __name__ == "__main__":
    import uvicorn
    # Initialize the system so it's ready to serve your analysis requests
    try:
        build_collection("routing_rules")
    except Exception as e:
        print("[API Start] System initialization log:", e)
        
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
