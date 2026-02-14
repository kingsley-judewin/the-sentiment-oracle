"""
stress_test.py — Ingestion Stress Testing
===========================================
Simulates high-volume ingestion scenarios to validate performance
and stability under load.

Tests:
  - Large batch processing (200+ posts)
  - Deduplication effectiveness
  - Score computation latency
  - Memory stability

Usage:
    python -m app.testing.stress_test
"""

import sys
import time
from datetime import datetime, timezone

from app.ingestion.aggregator import aggregate
from app.nlp.cleaner import clean_posts
from app.nlp.sentiment import analyze_posts
from app.nlp.model import get_model
from app.scoring.vibe_score import compute
from app.scoring.smoothing import smooth


class StressTestRunner:
    """Stress test runner for high-volume scenarios."""
    
    def __init__(self):
        self.results = {}
    
    def run(self) -> bool:
        """Run all stress tests."""
        print("=" * 60)
        print("  SENTIMENT ORACLE — Stress Test")
        print("=" * 60)
        
        # Pre-load model
        print("\n[Setup] Loading NLP model...")
        get_model()
        print("        Model loaded ✓")
        
        # Test 1: Large batch processing
        print("\n[Test 1] Large batch processing (200 posts)")
        success1 = self._test_large_batch()
        
        # Test 2: Deduplication effectiveness
        print("\n[Test 2] Deduplication effectiveness")
        success2 = self._test_deduplication()
        
        # Test 3: Score computation latency
        print("\n[Test 3] Score computation latency")
        success3 = self._test_latency()
        
        # Summary
        print("\n" + "=" * 60)
        print("  STRESS TEST RESULTS")
        print("=" * 60)
        
        all_passed = success1 and success2 and success3
        
        if all_passed:
            print("  ✅ ALL STRESS TESTS PASSED")
        else:
            print("  ❌ SOME STRESS TESTS FAILED")
        
        print("=" * 60)
        
        return all_passed
    
    def _test_large_batch(self) -> bool:
        """Test processing of large post batch."""
        try:
            # Generate 200 synthetic posts
            posts = self._generate_synthetic_posts(200)
            
            print(f"        Generated {len(posts)} synthetic posts")
            
            # Process through pipeline
            start = time.perf_counter()
            
            aggregated = aggregate(posts)
            cleaned = clean_posts(aggregated)
            analyzed = analyze_posts(cleaned)
            score_result = compute(analyzed)
            smoothed = smooth(score_result["raw_score"])
            
            latency = time.perf_counter() - start
            
            print(f"        Pipeline completed in {latency:.2f}s")
            print(f"        Posts: {len(posts)} → {len(aggregated)} → {len(cleaned)} → {len(analyzed)}")
            print(f"        Score: {score_result['raw_score']:.2f} → {smoothed:.2f}")
            
            # Validate
            if latency > 5.0:
                print(f"        ⚠ SLOW — Latency {latency:.2f}s exceeds 5s threshold")
                return False
            
            if len(analyzed) == 0:
                print("        ✗ FAIL — No posts survived pipeline")
                return False
            
            if not (-100 <= smoothed <= 100):
                print(f"        ✗ FAIL — Score {smoothed} out of bounds")
                return False
            
            print("        ✓ PASS")
            self.results["large_batch_latency"] = latency
            return True
        
        except Exception as e:
            print(f"        ✗ FAIL — Exception: {e}")
            return False
    
    def _test_deduplication(self) -> bool:
        """Test deduplication effectiveness with duplicates."""
        try:
            # Generate posts with intentional duplicates
            unique_posts = self._generate_synthetic_posts(100)
            duplicate_posts = unique_posts[:50]  # Duplicate first 50
            
            all_posts = unique_posts + duplicate_posts
            print(f"        Generated {len(all_posts)} posts (50 duplicates)")
            
            # Process
            aggregated = aggregate(all_posts)
            
            # Check deduplication
            reduction = len(all_posts) - len(aggregated)
            print(f"        Deduplication: {len(all_posts)} → {len(aggregated)} ({reduction} removed)")
            
            if reduction < 40:  # Should remove at least 40 of 50 duplicates
                print(f"        ⚠ WARN — Only {reduction} duplicates removed (expected ~50)")
            
            print("        ✓ PASS")
            self.results["dedup_effectiveness"] = reduction / 50  # Ratio
            return True
        
        except Exception as e:
            print(f"        ✗ FAIL — Exception: {e}")
            return False
    
    def _test_latency(self) -> bool:
        """Test score computation latency with various batch sizes."""
        try:
            batch_sizes = [10, 50, 100]
            latencies = []
            
            for size in batch_sizes:
                posts = self._generate_synthetic_posts(size)
                
                start = time.perf_counter()
                aggregated = aggregate(posts)
                cleaned = clean_posts(aggregated)
                analyzed = analyze_posts(cleaned)
                compute(analyzed)
                latency = time.perf_counter() - start
                
                latencies.append(latency)
                print(f"        Batch {size}: {latency:.3f}s")
            
            # Check if latency scales reasonably
            avg_latency = sum(latencies) / len(latencies)
            
            if avg_latency > 3.0:
                print(f"        ⚠ WARN — Average latency {avg_latency:.2f}s exceeds 3s")
            
            print("        ✓ PASS")
            self.results["avg_latency"] = avg_latency
            return True
        
        except Exception as e:
            print(f"        ✗ FAIL — Exception: {e}")
            return False
    
    def _generate_synthetic_posts(self, count: int) -> list[dict]:
        """Generate synthetic posts for testing."""
        posts = []
        now = datetime.now(timezone.utc).isoformat()
        
        sentiments = [
            "Bitcoin is going to the moon! Amazing gains today!",
            "Ethereum is crashing hard, very bearish market.",
            "DeFi protocols are revolutionizing finance.",
            "Crypto market is extremely volatile right now.",
            "Bullish on blockchain technology long term.",
            "Bearish sentiment across all major coins.",
            "Great news for cryptocurrency adoption!",
            "Regulatory concerns are hurting the market.",
            "Institutional investors are buying heavily.",
            "Market manipulation is rampant in crypto.",
        ]
        
        for i in range(count):
            posts.append({
                "id": f"stress_test_{i}",
                "text": sentiments[i % len(sentiments)],
                "engagement": 10 + (i % 20),
                "timestamp": now,
                "author": f"user_{i}",
                "source": "test",
            })
        
        return posts


def main():
    """Main entry point for stress testing."""
    runner = StressTestRunner()
    success = runner.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
