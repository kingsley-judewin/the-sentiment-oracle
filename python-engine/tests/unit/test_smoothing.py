"""
test_smoothing.py — EMA Volatility Dampening Verification
============================================================
Validates the Exponential Moving Average smoother guarantees:
  - First-call passthrough
  - Gradual convergence
  - Alpha sensitivity
  - No sudden spikes
"""

import pytest
from app.scoring.smoothing import Smoother


# ── Initial State ─────────────────────────────────────────────

class TestInitialState:
    def test_first_call_returns_raw(self):
        """First invocation should return the raw score unchanged."""
        s = Smoother(alpha=0.3)
        result = s.smooth(50.0)
        assert result == 50.0

    def test_initial_previous_is_none(self):
        s = Smoother(alpha=0.3)
        assert s.previous_score is None

    def test_after_first_call_previous_set(self):
        s = Smoother(alpha=0.3)
        s.smooth(50.0)
        assert s.previous_score == 50.0

    def test_history_starts_empty(self):
        s = Smoother(alpha=0.3)
        assert s.history == []

    def test_history_tracks_calls(self):
        s = Smoother(alpha=0.3)
        s.smooth(50.0)
        s.smooth(60.0)
        assert len(s.history) == 2


# ── Gradual Convergence ───────────────────────────────────────

class TestGradualConvergence:
    def test_new_score_changes_gradually(self):
        """After initial 0.0, a jump to 100.0 should NOT produce 100.0."""
        s = Smoother(alpha=0.3)
        s.smooth(0.0)   # initial = 0
        result = s.smooth(100.0)
        assert result < 100.0, "EMA should dampen sudden jumps"
        assert result > 0.0, "EMA should move toward new value"

    def test_repeated_same_input_converges(self):
        """Repeatedly feeding the same value should converge toward it."""
        s = Smoother(alpha=0.3)
        s.smooth(0.0)  # start at 0
        for _ in range(50):
            result = s.smooth(80.0)
        assert abs(result - 80.0) < 1.0, "Should converge to sustained input"

    def test_opposite_direction_dampened(self):
        """A swing from +100 to -100 should be dampened."""
        s = Smoother(alpha=0.3)
        s.smooth(100.0)
        result = s.smooth(-100.0)
        assert result > -100.0, "Swing should be dampened"
        assert result < 100.0


# ── Alpha Sensitivity ─────────────────────────────────────────

class TestAlphaSensitivity:
    def test_high_alpha_more_responsive(self):
        """Higher alpha = faster response to new data."""
        slow = Smoother(alpha=0.1)
        fast = Smoother(alpha=0.9)

        slow.smooth(0.0)
        fast.smooth(0.0)

        slow_result = slow.smooth(100.0)
        fast_result = fast.smooth(100.0)

        assert fast_result > slow_result, "Higher alpha should react faster"

    def test_alpha_zero_ignores_new(self):
        """Alpha=0 should completely ignore new input after first call."""
        s = Smoother(alpha=0.0)
        s.smooth(50.0)
        result = s.smooth(100.0)
        assert result == 50.0, "Alpha=0 should keep old value"

    def test_alpha_one_no_smoothing(self):
        """Alpha=1 should always return raw value."""
        s = Smoother(alpha=1.0)
        s.smooth(50.0)
        result = s.smooth(100.0)
        assert result == 100.0, "Alpha=1 should just return raw"


# ── No Sudden Spikes ──────────────────────────────────────────

class TestNoSuddenSpikes:
    def test_single_spike_absorbed(self):
        """A single spike in otherwise stable data should be absorbed."""
        s = Smoother(alpha=0.3)

        # Build up stable baseline at 0
        for _ in range(10):
            s.smooth(0.0)

        # Single extreme spike
        spike_result = s.smooth(100.0)

        # Should not jump to anywhere near 100
        assert spike_result < 50.0, "Single spike should be heavily dampened"

    def test_sustained_extreme_eventually_reaches(self):
        """Sustained extreme input should eventually reach near that value."""
        s = Smoother(alpha=0.3)
        s.smooth(0.0)

        for _ in range(100):
            result = s.smooth(100.0)

        assert result > 95.0, "Sustained input should converge"


# ── Output Type ───────────────────────────────────────────────

class TestOutputType:
    def test_returns_float(self):
        s = Smoother(alpha=0.3)
        result = s.smooth(42.0)
        assert isinstance(result, float)

    def test_rounded_to_two_decimals(self):
        s = Smoother(alpha=0.3)
        s.smooth(0.0)
        result = s.smooth(33.333333)
        # Result should be rounded
        assert result == round(result, 2)


# ── Isolation ─────────────────────────────────────────────────

class TestIsolation:
    def test_separate_instances_independent(self):
        """Two smoother instances should not share state."""
        a = Smoother(alpha=0.3)
        b = Smoother(alpha=0.3)

        a.smooth(100.0)
        b.smooth(-100.0)

        assert a.previous_score == 100.0
        assert b.previous_score == -100.0
