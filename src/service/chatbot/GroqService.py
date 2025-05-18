import json
from datetime import datetime

from src.model.dto import PostFilters
from src.models import Entity
from src.service.Logger import logger
from src.service.chatbot.llm import search_movies_schema, get_llm, search_movies_system_message
from src.service.recommendation.RecommendationService import recommendation_service
from src.util.util import str_to_date


class GroqService:

    def __init__(self, db):
        self.db = db
        self.llm = get_llm()
        self.rec = recommendation_service
        self.model = "llama-3.1-8b-instant"

    async def generate(self, user, history, text: str) -> str:
        history.insert(0, search_movies_system_message)

        logger.info(f"Generating response for user {user.user_id} with message: {text}")
        logger.info(f"History: {history}")

        first = await self._create(
                messages=history + [{"role": "user", "content": text}],
                tools=[search_movies_schema],
                tool_choice="auto",
        )

        logger.info(f"First response: {first}")

        choice = first.choices[0]
        if choice.finish_reason != "tool_calls":
            # The model wants a clarification; return its text directly.
            return choice.message.content

        filters = self._parse_json(choice.message.tool_calls[0].function.arguments)

        logger.info(f"Parsed filters: {filters}")

        candidate_ids = self._get_recommendations(user, filters)

        logger.info(f"Candidate IDs: {candidate_ids}")

        if not candidate_ids:
            return "I couldn’t find any titles that match. Could you refine your request?"

        movies = self._fetch_movies(candidate_ids)

        summary = "\n".join(
                f"- {m.title} ({str_to_date(m.release_date).strftime('%Y')}) \n "
                for m in movies if m.overview
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un asistente de recomendación de películas. "
                    "Responde en español con un tono breve, claro y amigable. "
                    "Formatea la respuesta para que se entienda bien. Una recomendacion por linea."
                    "Presenta las películas que recibas en el contexto, "
                    "sin mostrar JSON ni datos técnicos. "
                    "Puedes invitar al usuario a refinar la búsqueda o pedir más sugerencias."
                ),
            },
            {
                "role": "system",
                "name": "motor_recomendaciones",  # etiqueta opcional
                "content": "Películas recomendadas:\n\n" + summary,
            },
            {
                "role": "user",
                "content": "Preséntalas de forma clara.",
            },
        ]

        final = await self._create(messages=messages, temp=0.7)
        return final.choices[0].message.content

    async def _create(self, messages, tools=None, tool_choice=None, temp=0.0):
        args = {
            "model": self.model,
            "messages": messages,
            "temperature": temp
        }
        if tools:
            args["tools"] = tools
        if tool_choice:
            args["tool_choice"] = tool_choice

        return await self.llm.chat.completions.create(**args)

    def _fetch_movies(self, candidate_ids):
        movies = self.db.query(Entity).filter(Entity.tmbd_id.in_(candidate_ids)).all()
        return movies

    def _get_recommendations(self, user, filters):
        user_id = user.user_id

        recommendations = self.rec.get_recommendation(user_id, filters, 10)

        return recommendations

    def _parse_json(self, arguments):
        args = json.loads(arguments)
        logger.info(f"Parsed arguments: {args}")

        # Convert Mongo-style release_date to flat fields
        if "release_date" in args:
            rel = args["release_date"]
            if "$gte" in rel:
                args["min_release_date"] = self._convert_date_format(rel["$gte"])
            if "$lt" in rel:
                # Assuming exclusive upper bound → subtract one day if needed
                args["max_release_date"] = self._convert_date_format(rel["$lt"])
            del args["release_date"]

        return PostFilters(**args)

    def _convert_date_format(self,date_str):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except Exception:
            return None
