import os
import uuid
from typing import List
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder
from src.config import settings

def get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.openai_api_key
    )

def get_pinecone_index():
    if not settings.pinecone_api_key or not settings.pinecone_index_name:
        raise ValueError("Pinecone API key and Index Name must be set for Pinecone.")
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name)

from typing import List, Optional

def get_vector_store(vector_store_type: Optional[str] = None):
    embeddings = get_embeddings()
    v_type = vector_store_type or settings.vector_store_type
    
    if v_type == "pinecone":
        # We still return PineconeVectorStore just in case a generic script needs it,
        # but our custom logic will bypass this for ingestion/retrieval.
        os.environ["PINECONE_API_KEY"] = settings.pinecone_api_key or ""
        return PineconeVectorStore(
            index_name=settings.pinecone_index_name,
            embedding=embeddings
        )
    else:
        persist_directory = os.path.join(os.getcwd(), "data", "chroma_db")
        return Chroma(
            collection_name="rag_collection",
            embedding_function=embeddings,
            persist_directory=persist_directory
        )

def add_chunks_to_vectorstore(chunks: List[Document], vector_store_type: str = "chroma"):
    batch_size = 100
    
    if vector_store_type == "pinecone":
        # 1. Initialize Pinecone raw SDK
        index = get_pinecone_index()
        embeddings = get_embeddings()
        
        # 2. Initialize BM25 Sparse Encoder
        bm25 = BM25Encoder().default()
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [doc.page_content for doc in batch]
            
            # 3. Generate Dense Vectors
            dense_vectors = embeddings.embed_documents(texts)
            
            # 4. Generate Sparse Vectors
            sparse_vectors = bm25.encode_documents(texts)
            
            # 5. Format for Pinecone Bulk Upsert
            pinecone_vectors = []
            for doc, dense, sparse in zip(batch, dense_vectors, sparse_vectors):
                metadata = doc.metadata.copy()
                metadata["text"] = doc.page_content
                
                pinecone_vectors.append({
                    "id": str(uuid.uuid4()),
                    "values": dense,
                    "sparse_values": sparse,
                    "metadata": metadata
                })
                
            # 6. Bulk Upsert!
            index.upsert(vectors=pinecone_vectors)
    else:
        # Chroma fallback
        vector_store = get_vector_store(vector_store_type)
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            vector_store.add_documents(batch)
