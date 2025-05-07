import json

from src.models import Entity
from src.service.chatbot.llm import search_movies_schema, get_llm
from src.service.recommendation.RecommendationService import recommendation_service


class GroqService:

    def __init__(self, db):
        self.db = db
        self.llm = get_llm()
        self.rec = recommendation_service

    async def generate(self, user, history, text: str) -> str:
        first = await self.llm.chat.completions.create(
                model="llama-3-8b-8192",
                messages=history + [{"role": "user", "content": text}],
                tools=[search_movies_schema],
                tool_choice="auto",
                temperature=0.0,  # deterministic JSON
        )

        choice = first.choices[0]
        if choice.finish_reason != "tool_call":
            # The model wants a clarification; return its text directly.
            return choice.message.content

        filters = json.loads(choice.message.tool_call.arguments)

        candidate_ids = self._get_recommendations(user, filters)

        if not candidate_ids:
            return "I couldn’t find any titles that match. Could you refine your request?"

        movies = self._fetch_movies(candidate_ids)

        summary = "\n".join(
                f"{m.title} ({m.year}) – {m.overview[:150]}…" for m in movies
        )

        final = await self._create(
                messages=history + [
                    choice.message,
                    {"role": "tool", "name": "search_movies", "content": summary}
                ],
                tools=[],
                tool_choice="auto",
        )
        return final.choices[0].message.content

    async def _create(self, messages, tools, tool_choice):
        return await self.llm.chat.completions.create(
                model="llama-3-8b-8192",
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=0.5,  # deterministic JSON
        )


    def _fetch_movies(self, candidate_ids):
        movies = self.db.query(Entity).filter(Entity.tmbd_id.in_(candidate_ids)).all()
        return movies

    def _get_recommendations(self, user, filters):
        user_id = user.user_id
        filters = {k: v for k, v in filters.items() if v is not None}
        filters["user_id"] = user_id
        filters["seen"] = False

        # Get the recommendations from the recommendation service
        recommendations = self.rec.self.rec.get_recommended_movies(user, 10, filters)

        # Extract the IDs of the recommended movies
        candidate_ids = [rec.tmbd_id for rec in recommendations]

        return candidate_ids
