"""
mock_stream.py — Data Source Layer
====================================
Simulates incoming social posts for the oracle pipeline.
In production: replaced by Twitter API / Discord bot / Farcaster scraper.
"""

from datetime import datetime, timedelta
import random


def fetch_posts() -> list[dict]:
    """
    Returns a list of mock social post objects.

    Each post: { text, engagement, timestamp, author }
    """
    base_time = datetime.utcnow()

    posts = [
        # ── Strong Positive ──────────────────────────────────
        {
            "text": "This project is absolutely incredible, the team delivers every single time!",
            "engagement": 342,
            "timestamp": base_time - timedelta(minutes=2),
            "author": "crypto_whale_99",
        },
        {
            "text": "Just went all in, the fundamentals are rock solid and the roadmap is clear",
            "engagement": 218,
            "timestamp": base_time - timedelta(minutes=5),
            "author": "defi_degen",
        },
        {
            "text": "The community around this token is one of the best I have ever seen",
            "engagement": 189,
            "timestamp": base_time - timedelta(minutes=8),
            "author": "nft_collector",
        },
        {
            "text": "Massive partnership announcement coming soon, bullish vibes everywhere",
            "engagement": 410,
            "timestamp": base_time - timedelta(minutes=1),
            "author": "alpha_hunter",
        },
        {
            "text": "I love how transparent the devs are, weekly updates and real progress",
            "engagement": 156,
            "timestamp": base_time - timedelta(minutes=12),
            "author": "hodler_4_life",
        },

        # ── Strong Negative ──────────────────────────────────
        {
            "text": "This is a complete scam, the devs are dumping on retail investors",
            "engagement": 287,
            "timestamp": base_time - timedelta(minutes=3),
            "author": "bear_patrol",
        },
        {
            "text": "Worst investment I have ever made, the token keeps bleeding nonstop",
            "engagement": 195,
            "timestamp": base_time - timedelta(minutes=7),
            "author": "rekt_trader",
        },
        {
            "text": "The smart contract has critical vulnerabilities, do not trust this project",
            "engagement": 320,
            "timestamp": base_time - timedelta(minutes=4),
            "author": "security_researcher",
        },
        {
            "text": "Team went silent for weeks, classic rug pull pattern happening right now",
            "engagement": 265,
            "timestamp": base_time - timedelta(minutes=6),
            "author": "crypto_detective",
        },

        # ── Sarcasm / Tricky ─────────────────────────────────
        {
            "text": "Oh sure another moonshot token, because the last hundred worked out great",
            "engagement": 145,
            "timestamp": base_time - timedelta(minutes=15),
            "author": "sarcasm_king",
        },
        {
            "text": "Definitely buying more of this amazing coin that only goes down, brilliant",
            "engagement": 178,
            "timestamp": base_time - timedelta(minutes=10),
            "author": "dark_humor_degen",
        },

        # ── Spam / Low Quality ───────────────────────────────
        {
            "text": "🚀🚀🚀 TO THE MOON 🌕🌕🌕 BUY NOW!!!",
            "engagement": 12,
            "timestamp": base_time - timedelta(minutes=20),
            "author": "spam_bot_001",
        },
        {
            "text": "gm",
            "engagement": 3,
            "timestamp": base_time - timedelta(minutes=25),
            "author": "lazy_poster",
        },
        {
            "text": "Check out my new NFT collection at https://scamsite.xyz/mint",
            "engagement": 8,
            "timestamp": base_time - timedelta(minutes=22),
            "author": "nft_spammer",
        },
        {
            "text": "AAAAAA",
            "engagement": 1,
            "timestamp": base_time - timedelta(minutes=30),
            "author": "keyboard_smasher",
        },

        # ── Neutral / Mixed ─────────────────────────────────
        {
            "text": "The token price is holding steady, waiting for the next catalyst to decide",
            "engagement": 98,
            "timestamp": base_time - timedelta(minutes=11),
            "author": "patient_trader",
        },
        {
            "text": "Interesting technical analysis on the chart, could break either direction soon",
            "engagement": 134,
            "timestamp": base_time - timedelta(minutes=9),
            "author": "chart_wizard",
        },
        {
            "text": "New governance proposal is live, the community should definitely vote on this",
            "engagement": 167,
            "timestamp": base_time - timedelta(minutes=13),
            "author": "dao_participant",
        },
        {
            "text": "The staking rewards are actually pretty decent compared to other protocols",
            "engagement": 112,
            "timestamp": base_time - timedelta(minutes=14),
            "author": "yield_farmer",
        },
        {
            "text": "I have been following this project since day one and the growth is real",
            "engagement": 203,
            "timestamp": base_time - timedelta(minutes=16),
            "author": "og_supporter",
        },
        {
            "text": "Market is brutal right now but this project keeps building regardless",
            "engagement": 176,
            "timestamp": base_time - timedelta(minutes=18),
            "author": "diamond_hands",
        },
    ]

    # Shuffle to simulate real-world unordered ingestion
    random.shuffle(posts)
    return posts
