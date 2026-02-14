/**
 * PostsList.jsx — Display scrollable list of recent posts
 */

import { truncateText } from '../utils/sentimentUtils';

export function PostsList({ posts }) {
    if (!posts || !Array.isArray(posts)) {
        return (
            <div className="posts-list bg-gray-900/50 border border-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Recent Posts</h3>
                <div className="text-gray-500 text-center py-8">No posts available</div>
            </div>
        );
    }

    // Show only top 10 posts
    const displayPosts = posts.slice(0, 10);

    return (
        <div className="posts-list bg-gray-900/50 border border-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">
                Recent Posts ({displayPosts.length})
            </h3>

            <div className="space-y-3 max-h-[400px] overflow-y-auto custom-scrollbar">
                {displayPosts.map((post, index) => {
                    const sentiment = post?.sentiment;
                    const isPositive = sentiment?.raw_label === 'POSITIVE';
                    const isNegative = sentiment?.raw_label === 'NEGATIVE';

                    return (
                        <div
                            key={post?.id || index}
                            className="bg-black/30 border border-gray-800 rounded p-3 hover:border-gray-700 transition-colors"
                        >
                            <div className="flex items-start justify-between gap-3 mb-2">
                                {/* Sentiment Badge */}
                                <span
                                    className={`px-2 py-1 rounded text-xs font-semibold ${isPositive
                                        ? 'bg-green-500/20 text-green-500 border border-green-500/30'
                                        : isNegative
                                            ? 'bg-red-500/20 text-red-500 border border-red-500/30'
                                            : 'bg-gray-500/20 text-gray-500 border border-gray-500/30'
                                        }`}
                                >
                                    {sentiment?.raw_label || 'UNKNOWN'}
                                </span>

                                {/* Confidence & Engagement */}
                                <div className="flex items-center gap-3 text-xs text-gray-400">
                                    {sentiment?.confidence && (
                                        <span>
                                            {(sentiment.confidence * 100).toFixed(0)}% confident
                                        </span>
                                    )}
                                    {post?.engagement !== undefined && (
                                        <span className="flex items-center gap-1">
                                            <span>👍</span>
                                            {post.engagement}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {/* Post Text */}
                            <p className="text-gray-300 text-sm leading-relaxed">
                                {truncateText(post?.text, 150)}
                            </p>

                            {/* Polarity Score */}
                            {sentiment?.polarity_score !== undefined && (
                                <div className="mt-2 text-xs text-gray-500">
                                    Polarity: {sentiment.polarity_score > 0 ? '+' : ''}{sentiment.polarity_score}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
