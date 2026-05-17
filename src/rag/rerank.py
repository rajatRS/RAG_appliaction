from typing import List
from langchain_core.documents import Document
from src.rag.llm_client import call_responses_api
import re

def rerank_documents(query: str, docs: List[Document], top_k: int = 5) -> List[Document]:
    """
    Reranks documents using an LLM-as-a-judge approach via the responses API.
    """
    if not docs:
        return []

    scored_docs = []
    for doc in docs:
        prompt = f"""Rate the relevance of the following document to the given question on a scale of 0 to 10. 
        Only output the integer number, nothing else.

        Question: {query}
        Document: {doc.page_content}
        
        Score:"""
        
        try:
            # We use a fast, cheap model for scoring
            raw_score = call_responses_api(prompt, model_name="gpt-4o-mini").strip()
            # Extract just the first integer found
            match = re.search(r'\d+', raw_score)
            score = int(match.group()) if match else 0
        except Exception:
            score = 0
            
        # Store the rerank score in metadata
        doc.metadata["rerank_score"] = score
        scored_docs.append(doc)

    # Sort descending by rerank score
    scored_docs.sort(key=lambda x: x.metadata.get("rerank_score", 0), reverse=True)
    
    return scored_docs[:top_k]
