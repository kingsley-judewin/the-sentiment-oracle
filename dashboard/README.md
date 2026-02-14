# Sentiment Oracle Verification Dashboard

A lightweight React-based dashboard for validating the Sentiment Oracle backend in real-time.

## Features

- ✅ **Real-time Polling**: Auto-refreshes every 10 seconds
- ✅ **Sentiment Visualization**: Color-coded scores (green/red/yellow)
- ✅ **Live Posts Feed**: Shows recent posts with sentiment analysis
- ✅ **System Status**: Connection status, API latency, sentiment counts
- ✅ **Debug Panel**: Raw JSON payload inspection

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Start Backend

In a separate terminal:

```bash
cd ../python-engine
python app/main.py
```

Backend will run on `http://localhost:8000`

### 3. Start Dashboard

```bash
npm run dev
```

Dashboard will open at `http://localhost:5173`

## Architecture

```
src/
├── App.jsx                    # Main application layout
├── components/
│   ├── ScoreCard.jsx         # Sentiment score display
│   ├── PostsList.jsx         # Scrollable posts feed
│   └── StatusBar.jsx         # System status indicators
├── hooks/
│   └── useSentiment.js       # 10-second polling hook
└── utils/
    └── sentimentUtils.js     # Data processing utilities
```

## API Contract

The dashboard expects the backend to expose:

**GET** `http://localhost:8000/sentiment`

```json
{
  "community_vibe_score": -42,
  "raw_score": -38,
  "sample_size": 150,
  "posts": [
    {
      "text": "Sample post text...",
      "engagement": 42,
      "sentiment": {
        "raw_label": "POSITIVE",
        "confidence": 0.95,
        "polarity_score": 85
      }
    }
  ]
}
```

## Color Coding

| Score Range | Color | Meaning |
|-------------|-------|---------|
| ≥ 60 | 🟢 Green | Bullish |
| ≤ -60 | 🔴 Red | Bearish |
| -59 to 59 | 🟡 Yellow | Neutral |

## Verification Checklist

- [ ] Dashboard loads without errors
- [ ] Scores update every 10 seconds
- [ ] Sentiment colors match score ranges
- [ ] Posts list is scrollable
- [ ] Status bar shows connection state
- [ ] Error state displays when backend is down
- [ ] No console errors
- [ ] No memory leaks

## Tech Stack

- **React** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Native Fetch API** - HTTP requests

## Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Troubleshooting

### Backend Connection Failed

Make sure the Python backend is running:

```bash
cd ../python-engine
python app/main.py
```

### CORS Errors

The backend is configured to allow requests from `http://localhost:5173`. If you change the port, update the CORS settings in `python-engine/app/main.py`.

### No Data Showing

1. Check that backend is running on port 8000
2. Verify `/sentiment` endpoint returns data
3. Check browser console for errors

## Next Steps

After backend validation works:

1. Add contract event integration
2. Display Polygonscan transaction links
3. Add sentiment chart visualization
4. Enhance UI with professional design
