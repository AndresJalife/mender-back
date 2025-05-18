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
    "name": "search_movies",
    "description": (
        "Estás construyendo un sistema de recomendación de películas. "
        "Sos un asistente que intenta entender qué tipo de película quiere ver el usuario. "
        "Debés devolver un JSON con los filtros más relevantes para hacer recomendaciones. "
        "Si el mensaje es vago, hacé preguntas aclaratorias (máximo 5). "
        "No es necesario obtener todos los filtros; con los más importantes alcanza."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "genre": {
                "type": "array",
                "description": (
                    "Géneros principales que quiere ver el usuario, por ejemplo: ['Comedia'], ['Suspenso', 'Ciencia Ficción']. "
                    "Si el usuario menciona más de un género, incluirlos todos en el array. "
                    "Si no menciona ningún género, dejar vacío. "
                    "Usar strings con mayúscula inicial."
                )
            },
            "min_release_date": {
                "type": "string",
                "format": "date",
                "description": "Fecha mínima de estreno (formato: dd/mm/yyyy)."
            },
            "max_release_date": {
                "type": "string",
                "format": "date",
                "description": "Fecha máxima de estreno (formato: dd/mm/yyyy)."
            },
            "actors": {
                "type": "array",
                "description": (
                    "Lista de actores que el usuario quiere ver. Ejemplo: ['Tom Hanks']. "
                    "Si el usuario menciona más de uno, agregarlos todos. "
                    "Si no menciona actores, dejar vacío. "
                    "Intentá deducir el nombre del actor si el usuario lo sugiere implícitamente. "
                    "Formato esperado: 'Nombre Apellido'."
                )
            },
            "directors": {
                "type": "array",
                "description": (
                    "Lista de directores preferidos. Ejemplo: ['Steven Spielberg']. "
                    "Si hay más de uno, incluir todos. "
                    "Si no se menciona ninguno, dejar vacío. "
                    "Podés inferir el nombre si el usuario lo sugiere. "
                    "Formato: 'Nombre Apellido'."
                )
            },
            "original_language": {
                "type": "string",
                "description": (
                    "Idioma original de la película que quiere ver el usuario. "
                    "Ejemplo: 'es' para español, 'en' para inglés. "
                    "Si no se menciona, dejar vacío."
                )
            },
            "min_runtime": {
                "type": "integer",
                "description": (
                    "Duración mínima en minutos de la película. "
                    "Si no se menciona, dejar vacío."
                )
            },
            "max_runtime": {
                "type": "integer",
                "description": (
                    "Duración máxima en minutos de la película. "
                    "Si no se menciona, dejar vacío."
                )
            },
        }
    }
}
