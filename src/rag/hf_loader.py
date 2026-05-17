from datasets import load_dataset
from langchain_core.documents import Document
from typing import List, Dict, Any
from src.config import settings

def load_from_huggingface(dataset_name: str, split: str = "train", text_column: str = "text", metadata_columns: List[str] = None) -> List[Document]:
    """
    Load a dataset from Hugging Face and convert it to LangChain Documents.
    """
    if metadata_columns is None:
        metadata_columns = []
        
    # Load dataset
    dataset = load_dataset(dataset_name, split=split, token=settings.hf_token)
    
    docs = []
    for item in dataset:
        row: Dict[str, Any] = item  # type: ignore
        content = row.get(text_column, "")
        metadata = {"source": f"hf://{dataset_name}/{split}"}
        
        for col in metadata_columns:
            if col in row:
                metadata[col] = row[col]
                
        docs.append(Document(page_content=str(content), metadata=metadata))
        
    return docs
