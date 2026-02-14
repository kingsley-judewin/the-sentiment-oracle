/**
 * useSentiment.js — Custom hook for polling sentiment data
 */

import { useState, useEffect, useCallback } from 'react';
import { validateApiResponse } from '../utils/sentimentUtils';

const API_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/sentiment`;
const POLL_INTERVAL = 10000; // 10 seconds

export function useSentiment() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdated, setLastUpdated] = useState(null);
    const [latency, setLatency] = useState(null);

    const fetchSentiment = useCallback(async () => {
        const startTime = performance.now();

        try {
            const response = await fetch(API_URL);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const jsonData = await response.json();
            const endTime = performance.now();

            // Validate response structure
            const validation = validateApiResponse(jsonData);
            if (!validation.valid) {
                throw new Error(validation.error);
            }

            setData(jsonData);
            setError(null);
            setLastUpdated(new Date());
            setLatency(Math.round(endTime - startTime));
            setLoading(false);

        } catch (err) {
            console.error('Fetch error:', err);
            setError(err.message);
            setLoading(false);
            // Don't clear data on error - keep showing last valid data
        }
    }, []);

    useEffect(() => {
        // Initial fetch
        fetchSentiment();

        // Set up polling interval
        const intervalId = setInterval(fetchSentiment, POLL_INTERVAL);

        // Cleanup on unmount
        return () => {
            clearInterval(intervalId);
        };
    }, [fetchSentiment]);

    return {
        data,
        loading,
        error,
        lastUpdated,
        latency,
    };
}
