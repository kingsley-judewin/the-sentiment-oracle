"""
e2e_runtime_test.py — End-to-End Runtime Validation
=====================================================
Tests the complete sentiment oracle pipeline from ingestion to scoring.
Validates that all components work together correctly in production mode.

Usage:
    python -m app.testing.e2e_runtime_test
"""

import sys
import time
from datetime import datetime

from app.ingestion.source_router import get_posts
from app.ingestion.aggregator import aggregate
from app.nlp.cleaner import clean_posts
from app.nlp.sentiment import analyze_posts
from app.nlp.model import get_model
from app.scoring.vibe_score import compute
from app.scoring.smoothing import smooth, get_smoother
from app.monitoring import get_metrics


class E2ETestRunner:
    """End-to-end test runner for the sentiment oracle pipeline."""
    
    def __init__(self, cycles: int = 5):
        self.cycles = cycles
        self.results = []
        self.errors = []
    
    def run(self) -> bool:
        """
        Run end-to-end test with multiple cycles.
        
        Returns:
            True if all tests pass, False otherwise
        """
        print("=" * 60)
        print("  SENTIMENT ORACLE — End-to-End Runtime Test")
        print("=" * 60)
        print(f"  Running {self.cycles} pipeline cycles...")
        print("=" * 60)
        
        # Pre-load model
        print("\n[Setup] Loading NLP model...")
        start = time.perf_counter()
        try:
            get_model()
            load_time = time.perf_counter() - start
            print(f"        Model loaded in {load_time:.2f}s ✓")
        except Exception as e:
            print(f"        Model loading FAILED: {e}")
            return False
        
        # Run cycles
        for cycle_num in range(1, self.cycles + 1):
            print(f"\n[Cycle {cycle_num}/{self.cycles}] Running pipeline...")
            
            success = self._run_single_cycle(cycle_num)
            if not success:
                print(f"        Cycle {cycle_num} FAILED")
                return False
            
            print(f"        Cycle {cycle_num} PASSED ✓")
            
            # Brief pause between cycles
            if cycle_num < self.cycles:
                time.sleep(1)
        
        # Validate results
        print("\n" + "=" * 60)
        print("  VALIDATION")
        print("=" * 60)
        
        return self._validate_results()
    
    def _run_single_cycle(self, cycle_num: int) -> bool:
        """Run a single pipeline cycle and record results."""
        try:
            # 1. Ingestion
            raw_posts = get_posts()
            if len(raw_posts) == 0:
                self.errors.append(f"Cycle {cycle_num}: No posts ingested")
                return False
            
            # 2. Aggregation
            aggregated = aggregate(raw_posts)
            if len(aggregated) == 0:
                self.errors.append(f"Cycle {cycle_num}: Aggregation returned empty")
                return False
            
            # 3. Cleaning
            cleaned = clean_posts(aggregated)
            if len(cleaned) == 0:
                self.errors.append(f"Cycle {cycle_num}: Cleaning returned empty")
                return False
            
            # 4. Sentiment analysis
            analyzed = analyze_posts(cleaned)
            if len(analyzed) == 0:
                self.errors.append(f"Cycle {cycle_num}: Sentiment analysis returned empty")
                return False
            
            # Verify sentiment fields exist
            for post in analyzed[:3]:  # Check first 3
                if "label" not in post or "confidence" not in post:
                    self.errors.append(f"Cycle {cycle_num}: Missing sentiment fields")
                    return False
            
            # 5. Scoring
            score_result = compute(analyzed)
            raw_score = score_result.get("raw_score")
            
            if raw_score is None:
                self.errors.append(f"Cycle {cycle_num}: Score computation failed")
                return False
            
            # Verify score bounds
            if not (-100 <= raw_score <= 100):
                self.errors.append(f"Cycle {cycle_num}: Score {raw_score} out of bounds")
                return False
            
            # 6. Smoothing
            smoothed_score = smooth(raw_score)
            
            if not (-100 <= smoothed_score <= 100):
                self.errors.append(f"Cycle {cycle_num}: Smoothed score {smoothed_score} out of bounds")
                return False
            
            # Record results
            self.results.append({
                "cycle": cycle_num,
                "raw_posts": len(raw_posts),
                "cleaned_posts": len(cleaned),
                "analyzed_posts": len(analyzed),
                "raw_score": raw_score,
                "smoothed_score": smoothed_score,
                "positive_count": score_result.get("positive_count", 0),
                "negative_count": score_result.get("negative_count", 0),
            })
            
            return True
        
        except Exception as e:
            self.errors.append(f"Cycle {cycle_num}: Exception — {e}")
            return False
    
    def _validate_results(self) -> bool:
        """Validate accumulated results across all cycles."""
        all_passed = True
        
        # Test 1: All cycles completed
        print(f"\n[Test 1] All {self.cycles} cycles completed")
        if len(self.results) == self.cycles:
            print("         PASS ✓")
        else:
            print(f"         FAIL — Only {len(self.results)} cycles completed")
            all_passed = False
        
        # Test 2: Posts ingested in every cycle
        print("\n[Test 2] Posts ingested in every cycle")
        min_posts = min(r["raw_posts"] for r in self.results)
        if min_posts > 0:
            print(f"         PASS ✓ (min: {min_posts} posts)")
        else:
            print("         FAIL — Some cycles had 0 posts")
            all_passed = False
        
        # Test 3: Scores within bounds
        print("\n[Test 3] All scores within [-100, +100]")
        all_in_bounds = all(
            -100 <= r["raw_score"] <= 100 and -100 <= r["smoothed_score"] <= 100
            for r in self.results
        )
        if all_in_bounds:
            print("         PASS ✓")
        else:
            print("         FAIL — Some scores out of bounds")
            all_passed = False
        
        # Test 4: Smoothing applied
        print("\n[Test 4] Smoothing state exists")
        smoother = get_smoother()
        if smoother.previous_score is not None:
            print(f"         PASS ✓ (last score: {smoother.previous_score})")
        else:
            print("         FAIL — No smoothing state")
            all_passed = False
        
        # Test 5: Deduplication working
        print("\n[Test 5] Deduplication active")
        for result in self.results:
            if result["raw_posts"] > result["cleaned_posts"]:
                print(f"         PASS ✓ (dedup reduced posts)")
                break
        else:
            print("         WARN — No deduplication observed (may be normal)")
        
        # Test 6: Score stability (variance check)
        print("\n[Test 6] Score stability across cycles")
        scores = [r["smoothed_score"] for r in self.results]
        if len(scores) >= 3:
            score_range = max(scores) - min(scores)
            if score_range < 200:  # Reasonable variance
                print(f"         PASS ✓ (range: {score_range:.2f})")
            else:
                print(f"         WARN — High variance (range: {score_range:.2f})")
        
        # Test 7: Metrics tracking
        print("\n[Test 7] Metrics tracking active")
        metrics = get_metrics()
        if metrics.get("total_cycles", 0) > 0:
            print(f"         PASS ✓ (tracked {metrics['total_cycles']} cycles)")
        else:
            print("         FAIL — No metrics recorded")
            all_passed = False
        
        # Summary
        print("\n" + "=" * 60)
        if all_passed:
            print("  ✅ ALL TESTS PASSED")
        else:
            print("  ❌ SOME TESTS FAILED")
        
        if self.errors:
            print("\n  Errors:")
            for error in self.errors:
                print(f"    - {error}")
        
        print("=" * 60)
        
        return all_passed


def main():
    """Main entry point for end-to-end testing."""
    runner = E2ETestRunner(cycles=5)
    success = runner.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
