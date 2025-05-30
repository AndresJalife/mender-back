from __future__ import annotations

import json
import os
from typing import Any, Dict, List, MutableSequence, Sequence

import httpx
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import Database
from src.model.dto import PostFilters
from src.models import Entity, User
from src.service.Logger import logger
from src.service.recommendation.RecommendationService import (
    RecommendationService,
)
from src.util.util import str_to_date

###############################################################################
# Configuration & singletons
###############################################################################

GROK_MODEL = os.getenv("GROK_MODEL", "grok-3-mini")
GROK_API_KEY = os.getenv("GROQ_API_KEY")
GROK_ENDPOINT = os.getenv("GROK_ENDPOINT", "https://api.x.ai/v1")

RECOMMENDATION_K = int(os.getenv("REC_K", 10))
MAX_TOKENS = int(os.getenv("GROK_MAX_TOKENS", 800))
TEMPERATURE = float(os.getenv("GROK_TEMPERATURE", 0.3))

# One shared async HTTP client per process.
HTTP_CLIENT = httpx.AsyncClient(timeout=15)


###############################################################################
# Grok client wrapper (OpenAI compatible)
###############################################################################

class GrokClient:
    """Wrap de `openai.AsyncOpenAI` con verificación de clave."""

    def __init__(self, api_key: str | None, base_url: str):
        if not api_key:
            raise RuntimeError(
                "GROK_API_KEY / OPENAI_API_KEY no configurado – exportá la clave antes de iniciar.")
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=HTTP_CLIENT)

    async def chat(self, **kwargs):
        return await self._client.chat.completions.create(**kwargs)


GROK_CLIENT = GrokClient(GROK_API_KEY, GROK_ENDPOINT)

###############################################################################
# 1️⃣  SYSTEM PROMPT – reglas de comportamiento
###############################################################################

_SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Sos un asistente de películas. El usuario te va a contar qué tipo de película quiere ver. "
        "Tu trabajo es interpretar su pedido. "
        "Habla siempre en un texto claro que el usuario pueda entender y **siempre** en español. "
        "Nunca respondas en JSON ni en código, **salvo** cuando invoques la función `search_movies`, "
        "caso en el cual tu salida debe ser **solo** el objeto JSON que describe los filtros. "
        "Cuando ya comprendas lo que el usuario quiere, invocá `search_movies`. "
        "Podés hacer algunas preguntas breves si el mensaje no es claro, pero evitá exceder 3–4 repreguntas. "
        "No hace falta completar todos los filtros; incluí solo los que el usuario mencione o puedas inferir. "
        "Si un filtro ya está respondido, no lo repreguntes. Si preguntás, que sea solo por filtros faltantes."
    ),
}

###############################################################################
# 2️⃣  TOOL SCHEMA – cómo debe devolver los filtros
###############################################################################

_SEARCH_MOVIES_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_movies",
        "description": (
            "Sos un asistente de recomendación de películas. "
            "Tu tarea es devolver un **objeto JSON** con los filtros que el usuario menciona. "
            "No pidas muchos detalles; podés hacer preguntas breves solo si es necesario. "
            "Si tenés suficiente información, devolvé directamente los filtros sin seguir preguntando. "
            "No repitas ejemplos innecesarios. Sé breve y directo. "
            "Tenés que hablar siempre en español."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "genres": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de géneros que el usuario quiere ver, en inglés (e.g. ['Comedy']). "
                        "Incluí todos los que mencione; si no menciona ninguno, **no incluyas este campo**. "
                        "Los géneros deben estar Capitalizados (por ejemplo 'Science Fiction')."
                    ),
                },
                "min_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": (
                        "Fecha mínima de estreno en formato dd/mm/yyyy. "
                        "Si no se menciona, **no incluyas este campo**."
                    ),
                },
                "max_release_date": {
                    "type": "string",
                    "format": "date",
                    "description": (
                        "Fecha máxima de estreno en formato dd/mm/yyyy. "
                        "Si no se menciona, **no incluyas este campo**."
                    ),
                },
                "actors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de actores que el usuario quiere ver (formato 'Nombre Apellido'). "
                        "Si no se menciona ninguno, **no incluyas este campo**."
                    ),
                },
                "directors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de directores preferidos. "
                        "Si no se menciona ninguno, **no incluyas este campo**."
                    ),
                },
                "original_language": {
                    "type": "string",
                    "description": (
                        "Código ISO‑639‑1 del idioma original (por ejemplo 'es' para español). "
                        "Si no se menciona, **no incluyas este campo**."
                    ),
                },
                "min_runtime": {
                    "type": "integer",
                    "description": (
                        "Duración mínima en minutos. "
                        "Si no se menciona, **no incluyas este campo**."
                    ),
                },
                "max_runtime": {
                    "type": "integer",
                    "description": (
                        "Duración máxima en minutos. "
                        "Si no se menciona, **no incluyas este campo**."
                    ),
                },
            },
        },
    },
}

TOOLS: Sequence[Dict[str, Any]] = [_SEARCH_MOVIES_TOOL]


###############################################################################
# 3️⃣  Pydantic helpers
###############################################################################

class _ChatRequest(BaseModel):
    user: User
    history: List[Dict[str, str]]
    text: str

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
    }

    @field_validator("history")
    def _copy_history(cls, v: List[Dict[str, str]]):  # noqa: N805
        return list(v)


###############################################################################
# 4️⃣  Main service class
###############################################################################

class GrokServiceV2:  # pylint: disable=too-few-public-methods
    """Orquestador de chat ↔ LLM ↔ recomendador."""

    def __init__(self, db: AsyncSession, rec: RecommendationService):
        self._db = db
        self._rec = rec

    # ------------------------------------------------------------------
    async def generate(self, *, user: User, history: Sequence[Dict[str, str]], text: str) -> str:
        req = _ChatRequest(user=user, history=list(history), text=text)

        messages: MutableSequence[Dict[str, Any]] = [_SYSTEM_PROMPT]
        messages.extend(req.history)
        messages.append({"role": "user", "content": req.text})

        while True:
            logger.info(f"Calling Grok – messages={messages[-3:]}")
            try:
                llm_resp = await GROK_CLIENT.chat(
                    model=GROK_MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                )
            except Exception as exc:  # noqa: BLE001
                logger.info(f"Grok API failure: {exc}")
                return "Lo siento, hubo un error técnico. Intentá de nuevo más tarde."

            choice = llm_resp.choices[0]
            logger.info(f"Grok choice finish_reason={choice.finish_reason}")

            # a) LLM quiere usar la herramienta
            if choice.finish_reason == "tool_calls":
                # 👉 1. guardar el mensaje de la llamada para que Grok lo vea en el segundo paso
                messages.append(choice.message)

                # 👉 2. procesar la llamada y responder con JSON
                reply_json = await self._handle_tool_call(choice.message.tool_calls, user)
                logger.info(f"Function output={reply_json}")

                messages.append({"role": "function", "name": "search_movies", "content": reply_json})
                continue  # vuelve a comenzar el loop

            # b) LLM ya tiene respuesta definitiva
            final_text = (choice.message.content or "").strip()
            if not final_text:
                final_text = (
                    "No encontré nada que se ajuste exactamente. ¿Querés intentar con otros filtros?"
                )
            logger.info(f"Grok final reply={final_text}")
            return final_text

    # ------------------------------------------------------------------
    async def _handle_tool_call(self, calls: Sequence[Any], user: User) -> str:
        if not calls:
            return json.dumps({"error": "no_tool_call"})

        call = calls[0]
        if call.function.name != "search_movies":
            logger.info(f"Unknown tool name {call.function.name}", )
            return json.dumps({"error": "unknown_tool"})

        try:
            filters = PostFilters(**json.loads(call.function.arguments or "{}"))
            logger.info(f"Parsed filters={filters}", filters)
        except Exception as exc:  # noqa: BLE001
            logger.info(f"Invalid tool arguments: {exc}")
            return json.dumps({"error": "invalid_arguments"})

        try:
            candidate_ids = await self._rec.get_recommendations_async(user.user_id, filters, k=RECOMMENDATION_K)
        except Exception as exc:  # noqa: BLE001
            logger.info(f"Recommendation failure: {exc}", )
            return json.dumps({"error": "rec_failure"})

        if not candidate_ids:
            return json.dumps({"movies": [], "status": "no_results"})

        movies_q = await self._db.execute(Entity.__table__.select().where(Entity.tmbd_id.in_(candidate_ids)))
        rows = movies_q.fetchall()
        summary = [
            f"- {row.title} ({str_to_date(row.release_date).year if row.release_date else '?'})"
            for row in rows
        ]
        return json.dumps({"movies": summary, "status": "ok"})