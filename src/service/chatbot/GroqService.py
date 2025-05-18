import json

from src.model.dto import PostFilters
from src.models import Entity
from src.service.Logger import logger
from src.service.chatbot.llm import search_movies_schema, get_llm
from src.service.recommendation.RecommendationService import recommendation_service


class GroqService:

    def __init__(self, db):
        self.db = db
        self.llm = get_llm()
        self.rec = recommendation_service
        self.model = "llama3-8b-8192"

    async def generate(self, user, history, text: str) -> str:
        history.insert(0, self._get_system_msg())

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
                f"{m.title} ({m.year}) – {m.overview[:150]}…" for m in movies
        )

        final = await self._create(
                messages=history + [choice.message, {"role": "tool", "name": "search_movies", "content": summary}],
                tools=[],
                tool_choice="auto",
                temp=0.7,
        )

        logger.info(f"Final response: {final}")

        return final.choices[0].message.content

    def _get_system_msg(self):
        return {
          "role": "system",
          "content": (
            "You are a helpful movie assistant. The user will describe the type of movie "
            "they want to watch. Return a JSON object with appropriate search filters using "
            "the `search_movies` function. If the user's message is unclear, ask a clarifying question instead."
          )
        }


    async def _create(self, messages, tools, tool_choice, temp=0.0):
        return await self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temp,
        )

    def _fetch_movies(self, candidate_ids):
        movies = self.db.query(Entity).filter(Entity.tmbd_id.in_(candidate_ids)).all()
        return movies

    def _get_recommendations(self, user, filters):
        user_id = user.user_id

        recommendations = self.rec.get_recommendation(user_id, filters, 10)

        return recommendations

    def _parse_json(self, arguments):
        filters = PostFilters(**json.loads(arguments))
        return filters
