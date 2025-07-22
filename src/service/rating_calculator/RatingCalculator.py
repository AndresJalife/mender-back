from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from src.service.Logger import logger


###############################################################################
# Enum de tipos de feedback                                                    #
###############################################################################

class FeedbackType(Enum):
    LIKE = auto()
    WATCH_SECONDS = auto()
    MORE_INFO = auto()
    SAW_MOVIE = auto()
    CHATBOT_REC = auto()

###############################################################################
# Dataclass para representar un evento de feedback                             #
###############################################################################

@dataclass(frozen=True)
class Feedback:
    """Una interacción del usuario con un post/película."""

    kind: FeedbackType
    value: Optional[int | float] = None  # segundos vistos u otro dato numérico

###############################################################################
# Calculadora de rating implícito                                              #
###############################################################################

class RatingCalculator:
    _WEIGHTS = {
        FeedbackType.LIKE: (3.25, 0.75),
        FeedbackType.MORE_INFO: (3, 0.5),
        FeedbackType.SAW_MOVIE: (2.75, 0.25),
        FeedbackType.CHATBOT_REC: (2.75, 0.25),
    }

    # Rangos de segundos vistos → (base, addition)
    _WATCH_RANGES = [
        (0, 2000, None), # ignorar < 2 s
        (2000, 5000, (2.75, 0.25)),
        (5000, 30000, (3, 0.5)),
        (30000, float("inf"), (3.25, 0.75)),
    ]

    def calculate(self, feedbacks: List[Feedback], explicit_rating: Optional[float] = None) -> Optional[float]:
        if explicit_rating is not None:
            return explicit_rating

        bases: List[float] = []
        additions: List[float] = []

        for fb in feedbacks:
            base_add = self._weights_for(fb)
            if base_add is None:
                continue  # feedback ignorado (ej.: <2 s)

            base, add = base_add
            bases.append(base)
            additions.append(add)

        if not bases:
            return None

        rating = max(bases) + sum(additions)

        logger.info(f"Calculating implicit rating: bases={bases}, additions={additions}")
        logger.info("Feedbacks: " + ", ".join(str(fb) for fb in feedbacks))
        logger.info("Rating: " + str(min(rating, 5.0)))
        return min(rating, 5.0)

    def _weights_for(self, fb: Feedback) -> Optional[tuple[float, float]]:
        """Devuelve tupla (base, addition) o None si el feedback debe ignorarse."""
        if fb.kind == FeedbackType.WATCH_SECONDS:
            return self._watch_weights(fb.value)
        if fb.value != 1:
            return None
        return self._WEIGHTS.get(fb.kind)

    def _watch_weights(self, miliseconds: Optional[int | float]) -> Optional[tuple[float, float]]:
        if miliseconds is None:
            return None
        for lo, hi, weights in self._WATCH_RANGES:
            if lo <= miliseconds < hi:
                return weights
        return None

