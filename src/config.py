from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # OpenAI Settings
    openai_api_key: str = ""
    
    # Vector DB Settings
    vector_store_type: str = "chroma" # options: "chroma", "pinecone"
    
    # Pinecone Settings
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: Optional[str] = None
    pinecone_environment: Optional[str] = None
    
    # Hugging Face
    hf_token: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
