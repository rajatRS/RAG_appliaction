from typing import List
from langchain_core.documents import Document
from src.rag.llm_client import call_responses_api

def format_docs(docs: List[Document]):
    return "\n\n".join(f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}" for doc in docs)

def generate_answer(query: str, docs: List[Document], model_name: str = "gpt-3.5-turbo") -> str:
    """
    Generate an answer using the requested responses API.
    """
    context = format_docs(docs)
    
    prompt = f"""You are an assistant for question-answering tasks. 
    Use the following pieces of retrieved context to answer the question. 
    If you don't know the answer, just say that you don't know. 
    Use three sentences maximum and keep the answer concise.
    
    Question: {query} 
    
    Context: {context} 
    
    Answer:"""
    
    return call_responses_api(prompt, model_name=model_name)
