from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from src.api import services

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    search_type: str = "dense"
    model_name: str = "gpt-3.5-turbo"
    vector_store: str = "chroma"

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]

class LocalFolderRequest(BaseModel):
    folder_path: str
    metadata: Optional[str] = None
    vector_store: str = "chroma"

@router.post("/upload", summary="Upload multiple documents for RAG ingestion")
async def upload_documents(
    files: List[UploadFile] = File(...),
    metadata: Optional[str] = Form(None),
    vector_store: str = Form("chroma")
):
    try:
        result = await services.process_uploaded_files(files, metadata, vector_store)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-local-folder", summary="Ingest documents from a local folder path")
async def upload_local_folder(request: LocalFolderRequest):
    try:
        result = await services.process_local_folder(request.folder_path, request.metadata, request.vector_store)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse, summary="Query the RAG system")
async def query_system(request: QueryRequest):
    try:
        answer, sources = await services.process_query(
            request.query, 
            request.top_k, 
            request.search_type, 
            request.model_name,
            request.vector_store
        )
        return QueryResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate", summary="Run RAG Evaluation from an uploaded tests.jsonl file")
async def run_evaluation(
    file: UploadFile = File(...),
    top_k: int = Form(5),
    vector_store: str = Form("chroma"),
    model_name: str = Form("gpt-3.5-turbo")
):
    try:
        result = await services.process_evaluation(file, top_k, vector_store, model_name)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

