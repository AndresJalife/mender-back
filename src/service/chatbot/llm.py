# deps.py
import os
from groq import AsyncGroq  # async version powered by httpx


def get_llm():
    return AsyncGroq(
            api_key=os.getenv("GROQ_API_KEY"),
    )


search_movies_schema = {
    "name": "search_movies",
    "description": "Extracts structured search filters from user messages for movie recommendations.",
    "parameters": {
        "type": "object",
        "properties": {
            "genre": {
                "type": "string",
                "description": (
                    "The main genre of the movie the user wants, e.g. 'comedy', 'thriller', "
                    "'science fiction'. Use common movie genres."
                )
            },
            "min_release_date": {
                "type": "string",
                "format": "date",
                "description": "The earliest release date the movie should have, in YYYY-MM-DD format."
            },
            "max_release_date": {
                "type": "string",
                "format": "date",
                "description": "The latest release date the movie should have, in YYYY-MM-DD format."
            },
            "min_rating": {
                "type": "number",
                "minimum": 0,
                "maximum": 10,
                "description": "The minimum rating the user expects (scale 0 to 10)."
            },
            "max_rating": {
                "type": "number",
                "minimum": 0,
                "maximum": 10,
                "description": "The maximum acceptable rating (scale 0 to 10)."
            }
        },
        "required": []
    }
}

