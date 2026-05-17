import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    UnstructuredWordDocumentLoader,
    JSONLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_and_chunk_document(file_path: str, original_filename: str, extra_metadata: dict = None) -> List[Document]:
    """
    Load a document based on its extension, attach metadata, and chunk it.
    """
    ext = os.path.splitext(original_filename)[1].lower()
    
    if ext == '.pdf':
        loader = PyPDFLoader(file_path)
    elif ext == '.md':
        loader = TextLoader(file_path)
    elif ext == '.csv':
        loader = CSVLoader(file_path)
    elif ext == '.xlsx':
        loader = UnstructuredExcelLoader(file_path, mode="elements")
    elif ext == '.docx':
        loader = UnstructuredWordDocumentLoader(file_path, mode="elements")
    elif ext == '.json':
        # Default JSON loader extracting all text, can be customized with jq_schema
        loader = JSONLoader(file_path, jq_schema='.', text_content=False)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
        
    docs = loader.load()
    
    # Attach extra metadata
    if extra_metadata is None:
        extra_metadata = {}
    
    for doc in docs:
        doc.metadata["source"] = original_filename
        doc.metadata.update(extra_metadata)
        
    # Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = text_splitter.split_documents(docs)
    return chunks
