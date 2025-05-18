# deps.py
import os
from groq import AsyncGroq  # async version powered by httpx


def get_llm():
    return AsyncGroq(
            api_key=os.getenv("GROQ_API_KEY"),
    )

search_movies_system_message = {
    "role": "system",
    "content": (
        "Sos un asistente de películas. El usuario te va a contar qué tipo de película quiere ver. "
        "Tu trabajo es interpretar lo que dice."
        "Habla siempre en texto que el usuario pueda entender. Nunca con json o código. "
        "Cuando ya hayas entendido lo que el usuario quiere, utiliza la función `search_movies`."
        "Podés hacer algunas pocas preguntas si el mensaje no es claro, pero evitá preguntar demasiado. "
        "No hace falta que completes todos los filtros. "
        "Si ya tenes la respuesta para alguno de los filtros, no lo vuelvas a preguntar. "
        "Si queres hacer repreguntas, que sea de algun filtro que falta."
        "Tenes que hablar siempre en español"
    )
}

search_movies_schema = {
    "type": "function",
    "function": {
        "name": "search_movies",
        "description": (
            "Sos un asistente de recomendación de películas. "
            "Tu tarea es devolver un objeto JSON con los filtros que el usuario menciona. "
            "No pidas muchos detalles. Podes hacer algunas preguntas breves para refinar la búsqueda. "
            "Si tenés suficiente información, devolvé directamente los filtros sin seguir preguntando. "
            "No repitas ejemplos innecesarios. Sé breve y directo."
            "Tenes que hablar siempre en español"
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "genres": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de géneros que el usuario quiere ver. Ejemplos: ['Comedy'], ['Action', 'Science Fiction']. "
                        "La lista que devuelve debe estar en ingles."
                        "Si el usuario menciona más de uno, incluir todos. "
                        "Si no menciona ninguno, **no incluyas este campo**. "
                        "Los géneros deben estar en mayúscula inicial (por ejemplo: 'Comedy')."
                    )
                },
                "min_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": (
                        "Fecha mínima de estreno en formato dd/mm/yyyy. "
                        "No uses estructuras tipo MongoDB como $gte o $lt."
                        "Si no se menciona, **no incluyas este campo**."
                    )
                },
                "max_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": (
                        "Fecha máxima de estreno en formato dd/mm/yyyy. "
                        "No uses estructuras tipo MongoDB como $gte o $lt."
                        "Si no se menciona, **no incluyas este campo**."
                    )
                },
                "actors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de actores que el usuario quiere ver. Ejemplo: ['Tom Hanks']. "
                        "Si el usuario menciona más de uno, incluir todos. "
                        "Intentá inferir nombres incluso si el usuario no los dice explícitamente. "
                        "Formato: 'Nombre Apellido'."
                    )
                },
                "directors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de directores preferidos. Ejemplo: ['Christopher Nolan']. "
                        "Si no se menciona ninguno, **no incluyas este campo**. "
                        "Podés inferir nombres si el usuario hace referencias indirectas."
                    )
                },
                "original_language": {
                    "type": "string",
                    "description": (
                        "Código del idioma original de la película (por ejemplo, 'es' para español, 'en' para inglés). "
                        "Si no se menciona, **no incluyas este campo**."
                    )
                },
                "min_runtime": {
                    "type": "integer",
                    "description": (
                        "Duración mínima en minutos. Si no se menciona, **no incluyas este campo**."
                    )
                },
                "max_runtime": {
                    "type": "integer",
                    "description": (
                        "Duración máxima en minutos. Si no se menciona, **no incluyas este campo**."
                    )
                }
            }
        }
    }
}


