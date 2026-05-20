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

class AgentConfigRequest(BaseModel):
    name: str
    instructions: str
    model_name: str
    temperature: float
    knowledge_source: str

class AgentRunRequest(BaseModel):
    ticket_text: str

@router.get("/agent/config", summary="Retrieve active Agent configuration")
async def get_agent_configuration():
    try:
        return await services.get_agent_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/config", summary="Save or update Agent configuration")
async def update_agent_configuration(request: AgentConfigRequest):
    try:
        return await services.update_agent_config(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/dataset", summary="Upload CSV/JSON legacy resolution logs for the Agent")
async def upload_agent_dataset_file(file: UploadFile = File(...)):
    try:
        return await services.process_agent_dataset(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agent/run", summary="Run Agent triage on a new ticket")
async def run_agent_triage_process(request: AgentRunRequest):
    try:
        return await services.process_agent_triage(request.ticket_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orchestrator/run", summary="Run Multimodal Orchestration pipeline")
async def run_orchestration_diagnostics(
    ticket_text: str = Form(...),
    image_file: UploadFile = File(None),
    active_subagents: str = Form("[]")
):
    try:
        return await services.process_orchestrator_diagnostics(
            ticket_text=ticket_text,
            image_file=image_file,
            active_subagents_str=active_subagents
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class ArchiveCaseRequest(BaseModel):
    customer_name: str
    department: str
    issue_category: str
    priority: str
    issue_description: str
    resolution_steps: List[str]
    resolution_summary: str

@router.post("/orchestrator/archive", summary="Archive a resolved Orchestration case into Agent's training logs")
async def archive_orchestrator_case(request: ArchiveCaseRequest):
    try:
        return await services.archive_orchestrator_resolution(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

