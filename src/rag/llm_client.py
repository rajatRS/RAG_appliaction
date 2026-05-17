from openai import OpenAI
from src.config import settings

def call_responses_api(prompt: str, model_name: str = "gpt-4o-mini") -> str:
    """
    Calls the OpenAI API using the exact responses.create method requested.
    """
    client = OpenAI(api_key=settings.openai_api_key)
    
    response = client.responses.create(
        model=model_name,
        input=prompt
    )
    
    return response.output_text
