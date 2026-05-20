import os
import json
from typing import List, Dict, Any
from src.config import settings
from src.rag.llm_client import call_responses_api
from src.rag.retrieval import retrieve_documents

CONFIG_PATH = os.path.join(os.getcwd(), "data", "agent_config.json")
DATASET_PATH = os.path.join(os.getcwd(), "data", "agent_dataset.json")

def ensure_data_dir():
    os.makedirs(os.path.join(os.getcwd(), "data"), exist_ok=True)

def save_agent_config(config: Dict[str, Any]):
    ensure_data_dir()
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def load_agent_config() -> Dict[str, Any]:
    ensure_data_dir()
    if not os.path.exists(CONFIG_PATH):
        # Default config if none exists yet
        return {
            "name": "IT Incident Triage Agent",
            "instructions": "You are a professional IT Service Desk Triage Agent. Analyze verbose incoming user tickets, classify their priority, and synthesize a high-quality step-by-step resolution based on past matched legacy resolutions.",
            "model_name": "gpt-4o-mini",
            "temperature": 0.3,
            "knowledge_source": "vector_db"
        }
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_agent_dataset(dataset: List[Dict[str, Any]]):
    ensure_data_dir()
    with open(DATASET_PATH, "w") as f:
        json.dump(dataset, f, indent=2)

def load_agent_dataset() -> List[Dict[str, Any]]:
    ensure_data_dir()
    if not os.path.exists(DATASET_PATH):
        return []
    with open(DATASET_PATH, "r") as f:
        return json.load(f)

def find_local_matches(query: str, dataset: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """
    Performs a lightweight keyword similarity search across the local legacy incident logs.
    """
    if not dataset:
        return []
    
    query_words = set(query.lower().split())
    scored_items = []
    
    for item in dataset:
        # Check matching words in title, category, description, and resolution
        text_to_search = f"{item.get('title', '')} {item.get('description', '')} {item.get('category', '')} {item.get('resolution', '')}".lower()
        score = sum(1 for word in query_words if word in text_to_search)
        scored_items.append((score, item))
        
    # Sort by score descending
    scored_items.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored_items[:limit] if score > 0]

async def run_agent_triage(ticket_text: str) -> Dict[str, Any]:
    """
    Main Agent execution: 
    1. Loads config.
    2. Retrieves historical incident references (vector store or uploaded JSON dataset).
    3. Feeds context into the CoT LLM Prompt.
    4. Returns reasoning steps and final suggested resolution.
    """
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ts}] [Agent Engine] ⚙ Starting Agent triage execution...")

    config = load_agent_config()
    source = config.get("knowledge_source", "vector_db")
    model_name = config.get("model_name", "gpt-4o-mini")
    
    print(f"[{ts}] [Agent Engine] Loaded Config -> Name: '{config.get('name')}', Model: '{model_name}', Source: '{source}'")
    
    # 1. Retrieve Historical Context
    retrieved_context = ""
    matches_found = []
    
    if source == "vector_db":
        try:
            print(f"[{ts}] [Agent Engine] Querying Vector Store database...")
            # Query the active RAG vector database (Chroma/Pinecone)
            docs = retrieve_documents(ticket_text, k=3, search_type="hybrid" if settings.vector_store_type == "pinecone" else "dense", vector_store_type=settings.vector_store_type)
            print(f"[{ts}] [Agent Engine] Vector query successful. Retrieved {len(docs)} document references.")
            for doc in docs:
                retrieved_context += f"- REFERENCE DOC:\n  Content: {doc.page_content}\n  Source: {doc.metadata.get('source', 'System Knowledge')}\n\n"
                matches_found.append({
                    "title": doc.metadata.get("source", "Legacy Document"),
                    "resolution": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "confidence": float(doc.metadata.get("confidence_score", 0.90))
                })
        except Exception as e:
            print(f"[{ts}] [Agent Engine] ⚠ Error querying Vector DB in agent: {e}")
            retrieved_context = "No historical logs retrieved from Vector Database due to a query issue."
    else:
        # Query custom uploaded logs
        print(f"[{ts}] [Agent Engine] Scanning uploaded legacy incident logs dataset...")
        dataset = load_agent_dataset()
        local_matches = find_local_matches(ticket_text, dataset, limit=3)
        print(f"[{ts}] [Agent Engine] Keyword search found {len(local_matches)} matching legacy resolutions.")
        for idx, match in enumerate(local_matches, 1):
            retrieved_context += f"- HISTORICAL INCIDENT {idx}:\n  Title: {match.get('title')}\n  Category: {match.get('category')}\n  Description: {match.get('description')}\n  Resolution: {match.get('resolution')}\n\n"
            matches_found.append({
                "title": match.get("title", "Legacy Incident Log"),
                "resolution": match.get("resolution", ""),
                "confidence": 0.95 - (idx * 0.05)
            })
            
    if not retrieved_context:
        print(f"[{ts}] [Agent Engine] No historical log matches found. Falling back to zero-shot diagnostic advice.")
        retrieved_context = "No legacy incidents matches were found in the database. General troubleshooting advice should be applied."

    # 2. Formulate Chain-of-Thought (CoT) Prompt
    agent_name = config.get("name", "IT Incident Triage Agent")
    agent_instructions = config.get("instructions", "")
    
    print(f"[{ts}] [Agent Engine] Formulating Chain-of-Thought System Prompt structure...")
    prompt = f"""You are the following AI Agent:
    Agent Name: {agent_name}
    Instructions: {agent_instructions}
    
    You have received a new verbose incident ticket:
    ---
    TICKET: {ticket_text}
    ---
    
    Here is the retrieved legacy incident history / reference knowledge base:
    ---
    {retrieved_context}
    ---
    
    Your task is to analyze the ticket, review the historical incident reference resolutions, perform Chain-of-Thought triage, and output a structured response.
    
    You MUST respond STRICTLY with a valid JSON block containing these exact keys (no extra text, markdown wrapping like ```json is allowed if valid):
    {{
      "reasoning_steps": [
        "First step of reasoning (e.g., Analyzing incoming ticket keywords...)",
        "Second step of reasoning (e.g., Querying knowledge base and matching key error codes...)",
        "Third step of reasoning (e.g., Comparing current error with past Ticket #X...)",
        "Fourth step of reasoning (e.g., Synthesizing a customized resolution...)"
      ],
      "priority": "Critical" | "High" | "Medium" | "Low",
      "confidence": 0.0 to 1.0 (float indicating triage certainty),
      "category": "e.g., Database, Network, Hardware, Access Control, Software",
      "suggested_resolution": "Markdown formatted step-by-step resolution guide for the support engineer."
    }}
    """
    
    # 3. Call responses API
    print(f"[{ts}] [Agent Engine] Calling OpenAI Responses completion API endpoint (model: {model_name})...")
    raw_response = call_responses_api(prompt, model_name=model_name)
    
    # Clean up markdown formatting wrapping JSON if present
    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    try:
        parsed = json.loads(cleaned)
        print(f"[{ts}] [Agent Engine] ✓ Triage synthesis succeeded! Priority: {parsed.get('priority')}, Category: {parsed.get('category')}, Confidence: {parsed.get('confidence')}")
    except Exception as e:
        print(f"[{ts}] [Agent Engine] ⚠ Parsing Error: Failed to compile Agent CoT JSON: {e}")
        parsed = {
            "reasoning_steps": [
                "Analyzing new ticket details...",
                "Error processing structured output. Synthesizing fallback plan...",
                "Providing fallback advice based on direct legacy references."
            ],
            "priority": "Medium",
            "confidence": 0.50,
            "category": "General",
            "suggested_resolution": f"### Troubleshooting steps\n\nWe encountered a parsing issue with the Agent's structured output. However, here are the retrieved references:\n\n{retrieved_context}"
        }
        
    parsed["matches"] = matches_found
    return parsed
