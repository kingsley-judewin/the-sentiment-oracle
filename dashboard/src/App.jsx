/**
 * App.jsx — Main application component
 */

import { useSentiment } from './hooks/useSentiment';
import { ScoreCard } from './components/ScoreCard';
import { StatusBar } from './components/StatusBar';
import { PostsList } from './components/PostsList';

function App() {
  const { data, loading, error, lastUpdated, latency } = useSentiment();

  return (
    <div className="min-h-screen bg-[#111] text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-black/50 backdrop-blur">
        <div className="container mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold">
            Sentiment Oracle
            <span className="ml-3 text-sm font-normal text-gray-500 uppercase tracking-wide">
              Verification Mode
            </span>
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Loading State */}
        {loading && !data && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
              <p className="text-gray-400">Loading sentiment data...</p>
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        {data && (
          <div className="space-y-6">
            {/* Score Card */}
            <ScoreCard data={data} />

            {/* Status Bar */}
            <StatusBar
              data={data}
              error={error}
              lastUpdated={lastUpdated}
              latency={latency}
            />

            {/* Posts List */}
            <PostsList posts={data.posts} />

            {/* Debug Panel (Optional) */}
            <details className="bg-gray-900/30 border border-gray-800 rounded-lg p-4">
              <summary className="cursor-pointer text-sm text-gray-400 hover:text-white">
                🔍 Debug: Raw JSON Payload
              </summary>
              <pre className="mt-3 text-xs text-gray-500 overflow-x-auto bg-black/50 p-3 rounded">
                {JSON.stringify(data, null, 2)}
              </pre>
            </details>
          </div>
        )}

        {/* Error State (when no data) */}
        {!loading && !data && error && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-4">⚠️</div>
              <h2 className="text-xl font-semibold text-red-500 mb-2">
                Connection Failed
              </h2>
              <p className="text-gray-400 mb-4">{error}</p>
              <p className="text-sm text-gray-500">
                Make sure the backend is running at{' '}
                <code className="bg-gray-800 px-2 py-1 rounded">
                  http://localhost:8000
                </code>
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-12">
        <div className="container mx-auto px-6 py-4 text-center text-sm text-gray-500">
          Auto-refreshing every 10 seconds • Backend validation UI
        </div>
      </footer>
    </div>
  );
}

export default App;
