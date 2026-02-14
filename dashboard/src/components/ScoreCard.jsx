/**
 * ScoreCard.jsx — Display main sentiment scores
 */

import { getScoreColor, getScoreBgColor, clamp } from '../utils/sentimentUtils';

export function ScoreCard({ data }) {
    if (!data) return null;

    const vibeScore = clamp(data.community_vibe_score);
    const rawScore = clamp(data.raw_score);
    const sampleSize = data.sample_size || 0;

    return (
        <div className={`score-card ${getScoreBgColor(vibeScore)} border-2 rounded-lg p-6 transition-all duration-300`}>
            <div className="text-center">
                <h2 className="text-gray-400 text-sm uppercase tracking-wide mb-2">
                    Community Vibe Score
                </h2>
                <div className={`text-7xl font-bold ${getScoreColor(vibeScore)} transition-colors duration-500`}>
                    {vibeScore > 0 ? '+' : ''}{vibeScore}
                </div>

                <div className="mt-6 flex justify-center text-sm">
                    <div className="bg-black/30 rounded p-3 min-w-[200px]">
                        <div className="text-gray-400 mb-1">Raw Score</div>
                        <div className={`text-2xl font-semibold ${getScoreColor(rawScore)}`}>
                            {rawScore > 0 ? '+' : ''}{rawScore}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
