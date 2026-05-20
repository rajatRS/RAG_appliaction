from fastapi import UploadFile
import os
import tempfile
import json
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.rag.loaders import load_and_chunk_document
from src.rag.vector_store import add_chunks_to_vectorstore
from src.rag.retrieval import retrieve_documents
from src.rag.generation import generate_answer
import datetime

def _process_single_file(file_path: str, original_filename: str, extra_metadata: dict) -> List:
    return load_and_chunk_document(file_path, original_filename, extra_metadata)

async def process_uploaded_files(files: List[UploadFile], metadata_str: str = None, vector_store: str = "chroma") -> dict:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ts}] [Ingestion] Starting ingestion for {len(files)} uploaded files into '{vector_store}'...")
    total_chunks = 0
    processed_files = []
    
    extra_metadata = {}
    if metadata_str:
        extra_metadata = json.loads(metadata_str)

    temp_paths = []
    
    for file in files:
        filename = file.filename or "unknown.txt"
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_paths.append((temp_file.name, file.filename))

    all_chunks = []
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [Ingestion] Step 1/2: Parsing and chunking files using Multithreading (4 workers)...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_process_single_file, t_path, f_name, extra_metadata): f_name 
            for t_path, f_name in temp_paths
        }
        
        for future in as_completed(futures):
            f_name = futures[future]
            try:
                chunks = future.result()
                all_chunks.extend(chunks)
                processed_files.append(f_name)
            except Exception as e:
                print(f"Error processing {f_name}: {e}")

    for t_path, _ in temp_paths:
        if os.path.exists(t_path):
            os.remove(t_path)

    if all_chunks:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] [Ingestion] Step 2/2: Adding {len(all_chunks)} chunks to vector store...")
        add_chunks_to_vectorstore(all_chunks, vector_store_type=vector_store)
        total_chunks = len(all_chunks)

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [Ingestion] ✓ Ingestion Complete!")
    return {
        "message": f"Successfully ingested {len(processed_files)} files into {vector_store}.",
        "files": processed_files,
        "chunks_added": total_chunks
    }

async def process_local_folder(folder_path: str, metadata_str: str = None, vector_store: str = "chroma") -> dict:
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ts}] [Ingestion] Scanning local folder '{folder_path}' for ingestion into '{vector_store}'...")
    if not os.path.isdir(folder_path):
        raise ValueError(f"The path '{folder_path}' is not a valid directory.")
        
    extra_metadata = {}
    if metadata_str:
        extra_metadata = json.loads(metadata_str)
        
    supported_extensions = {'.pdf', '.csv', '.xlsx', '.docx', '.json', '.md'}
    file_paths = []
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if os.path.splitext(file)[1].lower() in supported_extensions:
                file_paths.append(os.path.join(root, file))
                
    all_chunks = []
    processed_files = []
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [Ingestion] Step 1/2: Found {len(file_paths)} files. Parsing and chunking using Multithreading...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_process_single_file, path, path, extra_metadata): path 
            for path in file_paths
        }
        
        for future in as_completed(futures):
            path = futures[future]
            try:
                chunks = future.result()
                all_chunks.extend(chunks)
                processed_files.append(path)
            except Exception as e:
                print(f"Error processing {path}: {e}")

    if all_chunks:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] [Ingestion] Step 2/2: Adding {len(all_chunks)} chunks to vector store...")
        add_chunks_to_vectorstore(all_chunks, vector_store_type=vector_store)

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [Ingestion] ✓ Local Folder Ingestion Complete!")
    return {
        "message": f"Successfully ingested {len(processed_files)} files from {folder_path} into {vector_store}.",
        "files_processed": len(processed_files),
        "chunks_added": len(all_chunks)
    }

async def process_query(query: str, top_k: int = 5, search_type: str = "dense", model_name: str = "gpt-3.5-turbo", vector_store: str = "chroma"):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ts}] [Query] Received question: '{query}'")
    print(f"[{ts}]   [Query] Step 1/3: Retrieving top {top_k} documents from {vector_store} ({search_type} search)...")
    docs = retrieve_documents(query, k=top_k, search_type=search_type, vector_store_type=vector_store)
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}]   [Query] Step 2/3: Generating answer using {model_name}...")
    answer = generate_answer(query, docs, model_name)
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}]   [Query] Step 3/3: Formatting sources and scores...")
    sources = []
    for doc in docs:
        c_score = doc.metadata.get("confidence_score", 0.0)
        r_score = doc.metadata.get("rerank_score", 0.0)
        score_display = f"Similarity: {c_score:.4f} | Rerank: {r_score}/10"
        
        sources.append({
            "source": doc.metadata.get("source", "Unknown"),
            "page_content": doc.page_content[:200] + "...",
            "confidence_score": score_display
        })
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [Query] ✓ Query processed successfully!")
    return answer, sources

async def process_evaluation(file: UploadFile, top_k: int = 5, vector_store: str = "chroma", model_name: str = "gpt-3.5-turbo"):
    from src.rag.evaluation import TestQuestion, run_full_evaluation
    import json
    
    content = await file.read()
    lines = content.decode('utf-8').strip().split('\n')
    
    tests = []
    for line in lines:
        if not line.strip(): continue
        data = json.loads(line)
        tests.append(TestQuestion(
            question=data["question"],
            keywords=data.get("keywords", []),
            reference_answer=data.get("reference_answer", ""),
            category=data.get("category", "General")
        ))
        
    results = run_full_evaluation(tests, k=top_k, vector_store=vector_store, model_name=model_name)
    
    return {"results": [r.model_dump() for r in results]}

async def get_agent_config() -> dict:
    from src.rag.agent import load_agent_config
    return load_agent_config()

async def update_agent_config(config_dict: dict) -> dict:
    from src.rag.agent import save_agent_config
    save_agent_config(config_dict)
    return {"message": "Agent configured successfully."}

async def process_agent_dataset(file: UploadFile) -> dict:
    from src.rag.agent import save_agent_dataset
    import csv
    import json
    
    content = await file.read()
    filename = file.filename or "dataset.json"
    
    dataset = []
    if filename.endswith(".csv"):
        import io
        stream = io.StringIO(content.decode("utf-8"))
        reader = csv.DictReader(stream)
        for row in reader:
            dataset.append({
                "title": row.get("title", "Legacy Incident Log"),
                "category": row.get("category", "General"),
                "description": row.get("description", ""),
                "resolution": row.get("resolution", "")
            })
    else:
        # Assume JSON
        try:
            raw_data = json.loads(content.decode("utf-8"))
            if isinstance(raw_data, list):
                dataset = raw_data
            else:
                dataset = [raw_data]
        except Exception as e:
            raise ValueError(f"Failed to parse JSON dataset: {e}")
            
    save_agent_dataset(dataset)
    return {
        "message": f"Successfully loaded legacy resolution dataset ({len(dataset)} items).",
        "items_count": len(dataset)
    }

async def process_agent_triage(ticket_text: str) -> dict:
    from src.rag.agent import run_agent_triage
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ts}] [Agent Engine] Executing triage agent on incoming ticket...")
    result = await run_agent_triage(ticket_text)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [Agent Engine] ✓ Triage completed!")
    return result

async def process_orchestrator_diagnostics(
    ticket_text: str,
    image_file: UploadFile = None,
    active_subagents_str: str = "[]"
) -> dict:
    import base64
    from src.rag.multimodal_orchestrator import run_orchestration_pipeline
    
    image_base64 = None
    if image_file:
        content = await image_file.read()
        image_base64 = base64.b64encode(content).decode("utf-8")
        
    try:
        active_subagents = json.loads(active_subagents_str)
    except Exception:
        active_subagents = [s.strip().lower() for s in active_subagents_str.split(",") if s.strip()]
        
    return await run_orchestration_pipeline(
        ticket_text=ticket_text,
        image_base64=image_base64,
        active_subagents=active_subagents
    )

async def archive_orchestrator_resolution(resolved_case: dict) -> dict:
    from src.rag.multimodal_orchestrator import archive_resolution_to_logs
    return archive_resolution_to_logs(resolved_case)
