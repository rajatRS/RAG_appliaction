from src.rag.vector_store import get_vector_store, get_pinecone_index, get_embeddings
from src.rag.rerank import rerank_documents
from src.rag.llm_client import call_responses_api
from src.config import settings
from typing import List, Dict, Any
from langchain_core.documents import Document
from pinecone_text.sparse import BM25Encoder
import datetime

def generate_multi_queries(query: str) -> List[str]:
    prompt = f"""You are an AI language model assistant. Your task is to generate 3 
    different versions of the given user question to retrieve relevant documents from a vector database. 
    By generating multiple perspectives on the user question, your goal is to help
    the user overcome some of the limitations of the distance-based similarity search.
    Provide these alternative questions separated by newlines, with no numbering or extra text.

    Original question: {query}"""
    response = call_responses_api(prompt)
    queries = [q.strip() for q in response.split('\n') if q.strip()]
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [Query Rewriter] Generated 3 Perspectives:")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    
    if query not in queries:
        queries.append(query)
        
    return queries

def retrieve_documents(query: str, k: int = 5, search_type: str = "dense", vector_store_type: str = "chroma") -> List[Document]:
    queries = generate_multi_queries(query)
    all_docs = []
    
    if vector_store_type == "pinecone":
        # Raw Pinecone SDK Querying
        index = get_pinecone_index()
        embeddings = get_embeddings()
        bm25 = BM25Encoder().default()
        
        # Calculate alpha for hybrid weighting (1.0 = pure dense, 0.0 = pure sparse)
        # However, Pinecone SDK doesn't natively take an alpha in python SDK v3 `query()` out-of-the-box 
        # unless doing manual interpolation, but wait, Pinecone's standard dotproduct with sparse_values 
        # just adds the dot products together! 
        # We will retrieve using whatever the user requested.
        
        for q in queries:
            query_kwargs: Dict[str, Any] = {
                "top_k": k,
                "include_metadata": True
            }
            
            if search_type in ["dense", "hybrid"]:
                query_kwargs["vector"] = embeddings.embed_query(q)
            else:
                # If pure sparse, we must pass a dummy vector of 0s because vector is technically required
                # Wait, Pinecone allows querying with ONLY sparse vectors if you pass a 0-filled vector
                dummy_dim = len(embeddings.embed_query("test"))
                query_kwargs["vector"] = [0.0] * dummy_dim
                
            if search_type in ["sparse", "hybrid"]:
                query_kwargs["sparse_vector"] = bm25.encode_queries(q)
                
            result = index.query(**query_kwargs)
            
            # Reconstruct LangChain Documents
            for match in result["matches"]:
                metadata = match.get("metadata", {})
                text = metadata.pop("text", "")
                
                doc = Document(page_content=text, metadata=metadata)
                doc.metadata["confidence_score"] = float(match.get("score", 0.0))
                all_docs.append(doc)
                
    else:
        # Chroma Retrieval
        vector_store = get_vector_store(vector_store_type)
        dense_retriever = vector_store.as_retriever(search_kwargs={"k": k})
        
        for q in queries:
            dense_docs = dense_retriever.invoke(q)
            all_docs.extend(dense_docs)
    
    # Deduplicate
    unique_docs = {}
    for doc in all_docs:
        unique_docs[doc.page_content] = doc
        
    deduped_docs = list(unique_docs.values())
    
    # Rerank
    reranked_docs = rerank_documents(query, deduped_docs, top_k=k)
    
    return reranked_docs
