/**
 * StatusBar.jsx — Display system status information
 */

import { formatTimestamp, countSentiments } from '../utils/sentimentUtils';

export function StatusBar({ data, error, lastUpdated, latency }) {
    const isConnected = !error && data;
    const sentimentCounts = data ? countSentiments(data.posts) : { positive: 0, negative: 0 };

    return (
        <div className="status-bar bg-gray-900/50 border border-gray-800 rounded-lg p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {/* Connection Status */}
                <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                    <span className="text-gray-400">Backend:</span>
                    <span className={isConnected ? 'text-green-500' : 'text-red-500'}>
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>

                {/* API Latency */}
                <div className="flex items-center gap-2">
                    <span className="text-gray-400">Latency:</span>
                    <span className="text-white">
                        {latency ? `${latency}ms` : 'N/A'}
                    </span>
                </div>

                {/* Sentiment Counts */}
                <div className="flex items-center gap-2">
                    <span className="text-gray-400">Sentiment:</span>
                    <span className="text-green-500">{sentimentCounts.positive} ↑</span>
                    <span className="text-gray-600">/</span>
                    <span className="text-red-500">{sentimentCounts.negative} ↓</span>
                </div>

                {/* Last Updated */}
                <div className="flex items-center gap-2">
                    <span className="text-gray-400">Updated:</span>
                    <span className="text-white">
                        {formatTimestamp(lastUpdated)}
                    </span>
                </div>
            </div>

            {/* Error Display */}
            {error && (
                <div className="mt-3 text-red-400 text-xs bg-red-500/10 border border-red-500/30 rounded p-2">
                    ⚠️ {error}
                </div>
            )}
        </div>
    );
}
