/**
 * sentimentUtils.js — Utility functions for sentiment data processing
 */

/**
 * Count positive and negative posts from the posts array
 */
export function countSentiments(posts) {
    if (!Array.isArray(posts)) return { positive: 0, negative: 0 };

    const positive = posts.filter(
        (post) => post?.sentiment?.raw_label === 'POSITIVE'
    ).length;

    const negative = posts.filter(
        (post) => post?.sentiment?.raw_label === 'NEGATIVE'
    ).length;

    return { positive, negative };
}

/**
 * Format timestamp to readable format
 */
export function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';

    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);

    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;

    return date.toLocaleTimeString();
}

/**
 * Clamp number to safe range
 */
export function clamp(value, min = -100, max = 100) {
    if (typeof value !== 'number' || isNaN(value)) return 0;
    return Math.max(min, Math.min(max, value));
}

/**
 * Validate API response structure
 */
export function validateApiResponse(data) {
    if (!data || typeof data !== 'object') {
        return { valid: false, error: 'Invalid response format' };
    }

    const requiredFields = ['community_vibe_score', 'raw_score', 'sample_size'];
    const missingFields = requiredFields.filter(field => !(field in data));

    if (missingFields.length > 0) {
        return {
            valid: false,
            error: `Missing fields: ${missingFields.join(', ')}`
        };
    }

    if (!Array.isArray(data.posts)) {
        return { valid: false, error: 'Posts must be an array' };
    }

    return { valid: true };
}

/**
 * Get color class based on score
 */
export function getScoreColor(score) {
    if (score >= 60) return 'text-green-500';
    if (score <= -60) return 'text-red-500';
    return 'text-yellow-500';
}

/**
 * Get background color class based on score
 */
export function getScoreBgColor(score) {
    if (score >= 60) return 'bg-green-500/10 border-green-500';
    if (score <= -60) return 'bg-red-500/10 border-red-500';
    return 'bg-yellow-500/10 border-yellow-500';
}

/**
 * Truncate text to specified length
 */
export function truncateText(text, maxLength = 100) {
    if (!text || typeof text !== 'string') return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}
