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
        "Tu tarea es devolver un objeto JSON con los filtros usando la función `search_movies`. "
        "Si no entendés del todo, podés hacer preguntas aclaratorias. Pero no hagas más de 5 preguntas. "
        "No hace falta que completes todos los filtros, con los más importantes es suficiente. "
        "Si ya hiciste 5 preguntas o tenés suficiente información, devolvé directamente los filtros."
    )
}

search_movies_schema = {
    "type": "function",
    "function": {
        "name": "search_movies",
        "description": (
            "Sos un asistente que ayuda a recomendar películas. "
            "Tu tarea es interpretar las preferencias del usuario y devolver un objeto JSON con los filtros que se usarán "
            "para generar una recomendación personalizada. "
            "Si el usuario no es claro, hacé preguntas aclaratorias (máximo 5). "
            "No es necesario completar todos los filtros: usá solo los más importantes según el mensaje."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de géneros que el usuario quiere ver. Ejemplos: ['Comedia'], ['Suspenso', 'Ciencia Ficción']. "
                        "Si el usuario menciona más de uno, incluir todos. "
                        "Si no menciona ninguno, dejar vacío. "
                        "Los géneros deben estar en mayúscula inicial (por ejemplo: 'Comedia')."
                    )
                },
                "min_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": (
                        "Fecha mínima de estreno en formato ISO (yyyy-mm-dd). "
                        "Si no se menciona, dejar vacío."
                    )
                },
                "max_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": (
                        "Fecha máxima de estreno en formato ISO (yyyy-mm-dd). "
                        "Si no se menciona, dejar vacío."
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
                        "Si no se menciona ninguno, dejar vacío. "
                        "Podés inferir nombres si el usuario hace referencias indirectas."
                    )
                },
                "original_language": {
                    "type": "string",
                    "description": (
                        "Código del idioma original de la película (por ejemplo, 'es' para español, 'en' para inglés). "
                        "Si no se menciona, dejar vacío."
                    )
                },
                "min_runtime": {
                    "type": "integer",
                    "description": (
                        "Duración mínima en minutos. Si no se menciona, dejar vacío."
                    )
                },
                "max_runtime": {
                    "type": "integer",
                    "description": (
                        "Duración máxima en minutos. Si no se menciona, dejar vacío."
                    )
                }
            }
        }
    }
}


