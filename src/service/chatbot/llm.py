# deps.py
import os
from groq import AsyncGroq  # async version powered by httpx


def get_llm():
    return AsyncGroq(
            api_key=os.getenv("GROQ_API_KEY"),
    )


search_movies_schema = {
    "name": "search_movies",
    "description": "Find movies that satisfy the user's constraints",
    "parameters": {
        "type": "object",
        "properties": {
            "genres": {"type": "array", "items": {"type": "string"}},
            "include_keywords": {"type": "array", "items": {"type": "string"}},
            "exclude_keywords": {"type": "array", "items": {"type": "string"}},
            "release_year_from": {"type": "integer"},
            "release_year_to": {"type": "integer"},
            "max_runtime": {"type": "integer"}
        },
        "required": ["genres"]
    }
}
