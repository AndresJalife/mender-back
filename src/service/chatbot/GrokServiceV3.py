# -*- coding: utf-8 -*-
"""Improved GrokServiceV2 – with better function-calling handling, retries, and logging."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, MutableSequence, Optional, Sequence

import httpx
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import Database
from src.model.dto import PostFilters
from src.models import Entity, User
from src.service.Logger import logger
from src.service.recommendation.RecommendationService import RecommendationService
from src.util.util import str_to_date

###############################################################################
# Configuration
###############################################################################

GROK_MODEL = os.getenv("GROK_MODEL", "grok-3-mini-fast")
GROK_API_KEY = (
    os.getenv("GROK_API_KEY")
    or os.getenv("GROQ_API_KEY")
    or os.getenv("OPENAI_API_KEY")
)
GROK_ENDPOINT = os.getenv("GROK_ENDPOINT", "https://api.x.ai/v1")

RECOMMENDATION_K = int(os.getenv("REC_K", 10))
MAX_TOKENS = int(os.getenv("GROK_MAX_TOKENS", 0)) or None
TEMPERATURE = float(os.getenv("GROK_TEMPERATURE", 0.3))

HTTP_CLIENT = httpx.AsyncClient(timeout=15)

###############################################################################
# Grok client
###############################################################################

class GrokClient:
    def __init__(self, api_key: str, base_url: str):
        if not api_key:
            raise RuntimeError("Definí GROK_API_KEY / GROQ_API_KEY / OPENAI_API_KEY.")
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=HTTP_CLIENT)

    async def chat(self, **kwargs):
        return await self._client.chat.completions.create(**kwargs)

GROK_CLIENT = GrokClient(GROK_API_KEY, GROK_ENDPOINT)

###############################################################################
# Tool schema
###############################################################################

class SearchMoviesArgs(BaseModel):
    genres: Optional[List[str]] = Field(None, description="Géneros en inglés, capitalizados")
    min_release_date: Optional[str] = Field(None, description="Fecha mínima dd/mm/yyyy")
    max_release_date: Optional[str] = Field(None, description="Fecha máxima dd/mm/yyyy")
    actors: Optional[List[str]] = Field(None, description="Actores 'Nombre Apellido'")
    directors: Optional[List[str]] = Field(None, description="Directores preferidos")
    original_language: Optional[str] = Field(None, description="Código ISO‑639‑1 (es, en…)")
    min_runtime: Optional[int] = Field(None, description="Duración mínima en minutos")
    max_runtime: Optional[int] = Field(None, description="Duración máxima en minutos")

SCHEMA: Dict[str, Any] = SearchMoviesArgs.model_json_schema()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_movies",
            "description": "Filtra películas según los criterios del usuario",
            "parameters": SCHEMA,
        },
    }
]

_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Sos un asistente de películas. Habla en español. "
        "Cuando tengas filtros suficientes, llama a la función `search_movies`. "
        "Podés hacer hasta 3 repreguntas si falta info."
    ),
}

_FINAL_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Sos un asistente de películas que responde con entusiasmo en español. "
        "Te dan una lista de películas recomendadas y vos redactás una respuesta en base a las películas."
        "No debería ser una respuesta muy larga. Un resumen de las películas a recomendar y el listado de películas en formato markdown."
    )
}

###############################################################################
# DTO
###############################################################################

class _ChatRequest(BaseModel):
    user: User
    history: List[Dict[str, Any]]
    text: str

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("history")
    def _copy(cls, v):  # noqa: N805
        return list(v)

###############################################################################
# Main service
###############################################################################

class GrokServiceV2:
    FALLBACK_MSG = "No encontré nada que se ajuste exactamente. ¿Querés intentar con otros filtros?"

    def __init__(self, db: Database, rec: RecommendationService):
        self.db = db
        self._rec = rec

    async def generate(self, *, user: User, history: Sequence[Dict[str, str]], text: str) -> str:
        req = _ChatRequest(user=user, history=list(history), text=text)

        base_messages: MutableSequence[Dict[str, Any]] = [_SYSTEM_PROMPT]
        base_messages.extend(req.history)
        base_messages.append({"role": "user", "content": req.text})

        for attempt in ("auto", "required"):
            messages = list(base_messages)

            tool_choice = (
                "auto"
                if attempt == "auto"
                else {"type": "function", "function": {"name": "search_movies"}}
            )

            logger.info(f"Calling Grok – tool_choice={tool_choice}")
            try:
                chat_kwargs = {
                    "model": GROK_MODEL,
                    "messages": messages,
                    "tools": TOOLS,
                    "tool_choice": tool_choice,
                    "temperature": TEMPERATURE,
                }
                if MAX_TOKENS:
                    chat_kwargs["max_tokens"] = MAX_TOKENS

                llm_resp = await GROK_CLIENT.chat(**chat_kwargs)
            except Exception as exc:
                logger.exception("Grok API failure")
                return "Lo siento, hubo un error técnico. Intentá de nuevo más tarde."

            choice = llm_resp.choices[0]

            logger.info(
                    f"Tokens: prompt={getattr(llm_resp.usage, 'prompt_tokens', '?')}, "
                    f"completion={getattr(llm_resp.usage, 'completion_tokens', '?')}"
            )

            # ✅ Handle tool call
            if choice.message.tool_calls:
                try:
                    tc = choice.message.tool_calls[0]
                    logger.info(f"tool_call: {tc.function.name} args={tc.function.arguments}")
                    args = tc.function.arguments
                    if isinstance(args, str):
                        args = json.loads(args)
                    filters = SearchMoviesArgs(**args)
                    return await self._reply_with_recommendations(user, filters)
                except Exception as exc:
                    logger.info(f"Invalid tool_call arguments: {exc}")
                    return self.FALLBACK_MSG

            # ✅ Handle repregunta
            content = (choice.message.content or "").strip()
            if content.endswith("?"):
                logger.info("Bot repregunta")
                return content

            # ❌ If it's the second attempt, give up
            if attempt == "required":
                logger.info("Second attempt failed, giving up.")
                return self.FALLBACK_MSG

            # 🌀 Otherwise: try again with `required`
            logger.info("No tool_call or repregunta; retrying with required...")

        return self.FALLBACK_MSG

    # ------------------------------------------------------------------
    async def _reply_with_recommendations(self, user: User, filters: SearchMoviesArgs) -> str:
        try:
            candidate_ids = await self._rec.get_recommendations_async(
                user.user_id, PostFilters(**filters.dict(exclude_none=True)), k=RECOMMENDATION_K)
        except Exception:
            logger.exception("Recommendation failure")
            return self.FALLBACK_MSG

        if not candidate_ids:
            return self.FALLBACK_MSG

        rows = self.db.query(Entity).filter(
            Entity.tmbd_id.in_(candidate_ids)
        ).all()

        summary = "\n".join(
            f"- {row.title} ({str_to_date(row.release_date).year if row.release_date else '?'})"
            for row in rows
        )

        MOVIES_PROMPT = {
            "role": "system",
            "content": (
                f"Estas son las películas recomendadas: {', '.join(summary)}. "
                "Generá una respuesta natural y entusiasta con eso."
            )
        }

        response = await GROK_CLIENT.chat(
                model=GROK_MODEL,
                messages=[_FINAL_SYSTEM_PROMPT, MOVIES_PROMPT],
                temperature=0.3
        )
        logger.info(f"Bot reply: {response.choices[0].message.content.strip()}")
        return response.choices[0].message.content.strip()
