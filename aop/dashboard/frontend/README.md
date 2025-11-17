# AOP Dashboard Frontend

React-based frontend for the AOP Dashboard.

## Development Setup

```bash
cd aop/dashboard/frontend
npm install
npm run dev
```

This will start the Vite dev server on http://localhost:5173

## Build for Production

```bash
npm run build
```

Builds the app to `../static/` directory which is served by FastAPI.

## Technology Stack

- **Framework:** React 18
- **Build Tool:** Vite
- **Charts:** Recharts (for analytics)
- **Trace Visualization:** React Flow (for trace graphs)
- **Styling:** Tailwind CSS
- **State Management:** React Context API

## Component Structure

```
src/
  App.jsx                 # Main app component
  main.jsx               # Entry point
  components/
    Sidebar.jsx           # Filters and navigation
    LiveFeed.jsx          # Real-time event feed
    EventCard.jsx         # Single event display
    TraceExplorer.jsx     # Trace visualization tab
    TraceTree.jsx         # React Flow trace graph
    AnalyticsDashboard.jsx # Stats and charts
    EventSearch.jsx       # Advanced search tab
```

## API Integration

Frontend calls FastAPI backend at http://localhost:8000/api/*

Endpoints:
- GET /api/agents - List agents
- GET /api/events - Query events
- GET /api/traces/{id} - Get trace
- GET /api/stats - Get statistics
- WS /ws - Real-time event stream

## Status

**Backend Complete ✓**
**Frontend:** Coming in Week 12

For now, the dashboard serves a placeholder HTML page.
