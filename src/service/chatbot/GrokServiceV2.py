# -*- coding: utf-8 -*-
"""GrokServiceV2 – versión extendida con tool_call "ask_user" para repreguntas."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, MutableSequence, Optional, Sequence

import httpx
from pydantic import BaseModel, Field, field_validator

from src.config.database import Database
from src.model.dto import PostFilters
from src.models import Entity, User, Post
from src.service.Logger import logger
from src.service.recommendation.RecommendationService import RecommendationService
from src.util.util import str_to_date

###############################################################################
# Configuración
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
TEMPERATURE = float(os.getenv("GROK_TEMPERATURE", 0.4))

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
# Tool schemas
###############################################################################

class AskUserArgs(BaseModel):
    question: str = Field(..., description="Pregunta concreta para el usuario, en español")

class SearchMoviesArgs(BaseModel):
    genres: Optional[List[str]] = Field(None, description="Géneros en inglés, capitalizados")
    min_release_date: Optional[str] = Field(None, description="Fecha mínima dd/mm/yyyy")
    max_release_date: Optional[str] = Field(None, description="Fecha máxima dd/mm/yyyy")
    actors: Optional[List[str]] = Field(None, description="Actores 'Nombre Apellido'")
    directors: Optional[List[str]] = Field(None, description="Directores preferidos")
    original_language: Optional[str] = Field(None, description="Código ISO‑639‑1 (es, en…)")
    min_runtime: Optional[int] = Field(None, description="Duración mínima en minutos")
    max_runtime: Optional[int] = Field(None, description="Duración máxima en minutos")

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "Solicita al usuario un dato faltante y cierra el turno",
            "parameters": AskUserArgs.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_movies",
            "description": "Filtra películas según los criterios del usuario",
            "parameters": SearchMoviesArgs.model_json_schema(),
        },
    },
]

###############################################################################
# Prompts
###############################################################################

_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Sos un asistente de películas. Habla en español. "
        "Intenta hacer alguna repregunta para obtener más información, pero no mucha"
        "Si el usuario da solo información de uno de los filtros, solicitá datos extra."
        "Cuando necesites datos extra llamá a la función `ask_user` con un parámetro `question`. "
        "Una vez que tengas filtros suficientes llamá a `search_movies`. "
        "Podés encadenar como máximo tres repreguntas antes de decidirte."
    ),
}

_FINAL_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Sos un asistente de películas que responde con entusiasmo en español. "
        "Te dan una lista de películas recomendadas y vos redactás una respuesta breve y amigable en formato markdown.."
    ),
}

###############################################################################
# DTO interno
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
# Servicio principal
###############################################################################

class GrokServiceV2:
    FALLBACK_MSG = "No encontré nada que se ajuste exactamente. ¿Querés intentar con otros filtros?"

    def __init__(self, db: Database, rec: RecommendationService):
        self.db = db
        self._rec = rec

    async def generate(self, *, user: User, history: Sequence[Dict[str, str]], text: str):
        """Procesa un turno del chat y devuelve `(respuesta, entidades)`.
        Si la respuesta es una repregunta, `entidades` es `None`."""
        req = _ChatRequest(user=user, history=list(history), text=text)

        messages: MutableSequence[Dict[str, Any]] = [_SYSTEM_PROMPT]
        messages.extend(req.history)
        messages.append({"role": "user", "content": req.text})

        chat_kwargs = {
            "model": GROK_MODEL,
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "temperature": TEMPERATURE,
        }
        if MAX_TOKENS:
            chat_kwargs["max_tokens"] = MAX_TOKENS

        try:
            llm_resp = await GROK_CLIENT.chat(**chat_kwargs)
        except Exception as exc:
            logger.error(f"Grok API failure {exc}")
            return self.FALLBACK_MSG, None

        choice = llm_resp.choices[0]
        logger.info(
            f"Tokens: prompt={getattr(llm_resp.usage, 'prompt_tokens', '?')}, "
            f"completion={getattr(llm_resp.usage, 'completion_tokens', '?')}"
        )

        # ------------------------------------------------------------------
        # ── tool_call ──────────────────────────────────────────────────────
        # ------------------------------------------------------------------
        if choice.message.tool_calls:
            tc = choice.message.tool_calls[0]
            name = tc.function.name
            args_raw = tc.function.arguments
            logger.info(f"tool_call: {name} args={args_raw}")

            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except TypeError:
                args = args_raw or {}

            # ▸ repregunta ---------------------------------------------------
            if name == "ask_user":
                question = AskUserArgs(**args).question.strip()
                logger.info(f"ASK_USER → {question}")
                return question, None

            # ▸ búsqueda -----------------------------------------------------
            if name == "search_movies":
                filters = SearchMoviesArgs(**args)
                return await self._reply_with_recommendations(user, filters)

            # Si llega una tool desconocida devolvemos fallback
            logger.warning(f"Unknown tool_call: {name}")
            return self.FALLBACK_MSG, None

        # ------------------------------------------------------------------
        # ── texto libre (sólo debería ocurrir para mensajes finales) ───────
        # ------------------------------------------------------------------
        content = (choice.message.content or "").strip()
        logger.info(f"Bot reply: {content}")
        return content, None

    # ----------------------------------------------------------------------
    async def _reply_with_recommendations(self, user: User, filters: SearchMoviesArgs):
        try:
            candidate_ids = await self._rec.get_recommendations_async(
                user.user_id,
                PostFilters(**filters.dict(exclude_none=True)),
                k=RECOMMENDATION_K,
            )
        except Exception as e:
            logger.error(f"Recommendation failure {e}")
            return self.FALLBACK_MSG, None

        if not candidate_ids:
            return self.FALLBACK_MSG, None

        rows = (
            self.db.query(Entity.title, Entity.release_date, Post.post_id)
            .join(Post, Post.entity_id == Entity.entity_id)
            .filter(Entity.tmbd_id.in_(candidate_ids))
            .all()
        )

        summary = ", ".join(
            f"{title} ({str_to_date(release_date).year if release_date else '?'})" for title, release_date, _ in rows
        )

        MOVIES_PROMPT = {
            "role": "system",
            "content": (
                f"Estas son las películas recomendadas: {summary}. "
                "Generá una respuesta natural y entusiasta con eso."
            ),
        }

        response = await GROK_CLIENT.chat(
            model=GROK_MODEL,
            messages=[_FINAL_SYSTEM_PROMPT, MOVIES_PROMPT],
            temperature=0.3,
        )
        reply = response.choices[0].message.content.strip()
        logger.info(f"Bot final reply: {reply}")
        return reply, rows
