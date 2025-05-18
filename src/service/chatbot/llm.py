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
            "We are making a movie recommendation system. You are a bot that will try to understand what the user want to watch."
            "You have to ask clarifying questions if the user is not clear."
            "You will create a JSON response that contains the filters that will be used to search for movies."
            "Try not to ask too many questions, but if you need more information, ask them."
            "Try not to ask more than 5 questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "array",
                    "description": (
                        "The main genre of the movie the user wants, e.g. ['Comedy'], "
                        "['Thriller', 'Science Fiction']."
                        "If the user wants to see more than one genre, separate them with commas."
                        "If the user doesn't mention any genre, leave this field empty."
                        "The format of the genre should be a array of strings capitalized."
                    )
                },
                "min_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Earliest release date of the movie (dd/mm/yyyy)."
                },
                "max_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Latest release date of the movie (dd/mm/yyyy)."
                },
                "actors": {
                    "type": "array",
                    "description": (
                        "List of names of the actors the user wants to see in the movie, e.g. ['Tom Hanks']."
                        "If the user wants to see more than one actor, separate them with commas."
                        "If the user doesn't mention any actor, leave this field empty."
                        "You can try to guess the actor's name from the user's message."
                        "The format of the name should be 'First Last'."
                    )
                },
                "directors": {
                    "type": "array",
                    "description": (
                        "List of names of the directors the user wants to see in the movie, e.g. ['Steven Spielberg']."
                        "If the user wants to see more than one director, separate them with commas."
                        "If the user doesn't mention any director, leave this field empty."
                        "You can try to guess the director's name from the user's message."
                        "The format of the name should be 'First Last'."
                    )
                },
                "original_language": {
                    "type": "string",
                    "description": (
                        "The original language of the movie the user wants to watch, e.g. 'en', 'sp'."
                        "If the user doesn't mention any language, leave this field empty."
                    )
                },
            }
        }
    }
}
