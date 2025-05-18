# deps.py
import os
from groq import AsyncGroq  # async version powered by httpx


def get_llm():
    return AsyncGroq(
            api_key=os.getenv("GROQ_API_KEY"),
    )

search_movies_schema = {
    "type": "function",
    "function": {
        "name": "search_movies",
        "description": (
            "Return a list of up to 10 movies that match the given filters, "
            "ordered by the best recommendation score for the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "string",
                    "description": (
                        "The main genre of the movie the user wants, e.g. 'comedy', "
                        "'thriller', 'science fiction'."
                    )
                },
                "min_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Earliest release date (YYYY‑MM‑DD)."
                },
                "max_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Latest release date (YYYY‑MM‑DD)."
                },
                "min_rating": {
                    "type": "number", "minimum": 0, "maximum": 10,
                    "description": "Minimum rating (0‑10 scale)."
                },
                "max_rating": {
                    "type": "number", "minimum": 0, "maximum": 10,
                    "description": "Maximum rating (0‑10 scale)."
                }
            }
        }
    }
}
