"""
smoothing.py — Volatility Dampening Layer
============================================
Applies Exponential Moving Average (EMA) to prevent sudden extreme
spikes from single viral posts. Mandatory for serious oracle behavior.
"""

from app.config import EMA_ALPHA


class Smoother:
    """
    Stateful EMA smoother.

    Formula:
        smoothed = alpha * raw + (1 - alpha) * previous

    The first call returns the raw score unchanged (no history to blend).
    """

    def __init__(self, alpha: float = EMA_ALPHA):
        self.alpha = alpha
        self._previous_score: float | None = None
        self._history: list[float] = []

    def smooth(self, raw_score: float) -> float:
        """
        Apply EMA smoothing to the raw score.

        Returns smoothed score.
        """
        if self._previous_score is None:
            smoothed = raw_score
        else:
            smoothed = self.alpha * raw_score + (1 - self.alpha) * self._previous_score

        smoothed = round(smoothed, 2)
        self._previous_score = smoothed
        self._history.append(smoothed)

        return smoothed

    @property
    def previous_score(self) -> float | None:
        return self._previous_score

    @property
    def history(self) -> list[float]:
        return list(self._history)


# ── Global singleton ────────────────────────────────────────
_smoother = Smoother()


def smooth(raw_score: float) -> float:
    """Apply EMA smoothing using the global smoother instance."""
    return _smoother.smooth(raw_score)


def get_smoother() -> Smoother:
    """Return the global smoother for inspection."""
    return _smoother


def get_last_score() -> float | None:
    """Get the last smoothed score (for health checks)."""
    return _smoother.previous_score


def has_history() -> bool:
    """Check if smoother has any history (for health checks)."""
    return len(_smoother.history) > 0
