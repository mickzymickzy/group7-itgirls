# Route Planner (Graphhopper) – Project Activity 3, Option 1

Enhanced version of Lab 4.9.2. A **Python (Flask)** backend wraps the lab's Graphhopper
geocoding + routing logic; a **React (Vite)** frontend shows directions, a map and unit options. The original terminal app is kept as an upgraded CLI.

![screenshot](docs/screenshot.png)

## Features
- Vehicle profiles: car, bike, walk (free-plan Graphhopper profiles)
- Units toggle: miles / km / both (instant – the API returns both)
- Directions table with arrows, per-step distance and time; total distance, `hh:mm:ss` duration, climb/descent
- Interactive map (Leaflet + OpenStreetMap) with route line
- Swap start/destination, recent searches (browser localStorage)
- Friendly errors: empty input, unknown place, bad API key, no route, network failure
- Demo mode (`GRAPHHOPPER_KEY=demo`) – works offline with sample data (Washington ↔ Baltimore)

## Project layout
```
backend/gh_client.py   Core logic (lab code refactored): geocode(), route(), formatting helpers
backend/app.py         Flask API: /api/health, /api/profiles, POST /api/directions; serves the React build
backend/cli.py         Terminal version (colors, table, units)
backend/tests/         Unit tests (no network needed)
frontend/src/          React app: App.jsx (UI), MapView.jsx (map), api.js (calls backend)
docs/                  Backlog, completed rubric, screenshot
```

## Setup
Get a free key at https://www.graphhopper.com/ (Sign Up -> API Keys). **Never commit your key.**
Needs Python 3 and Node.js (nodejs.org). Use two terminals.

```bash
# Terminal 1 - backend
cd backend
pip install -r requirements.txt
export GRAPHHOPPER_KEY=your_key        # Windows PowerShell: $env:GRAPHHOPPER_KEY="your_key"
python app.py                          # API on http://localhost:5000

# Terminal 2 - frontend (hot reload)
cd frontend
npm install
npm run dev                            # open http://localhost:5173
```
No key yet? Use `GRAPHHOPPER_KEY=demo` for sample data (Washington <-> Baltimore only).
Alternative: `npm run build` once, then open http://localhost:5000 (Flask serves the built app).
Terminal version: `cd backend && python cli.py`. Tests: `cd backend && python -m unittest discover tests`.

## How it works (for the next team)
1. React sends `POST /api/directions {start, end, profile}`.
2. `gh_client.get_directions()` geocodes both places (`geocode()` = lab's geocoding function),
   calls the routing API with `points_encoded=false` (so the route is plain coordinates),
   then `add_units()` adds km, miles and `hh:mm:ss` to every step.
3. Errors raise `GraphhopperError(message, status)`; Flask returns `{error: ...}` and React shows it.

Changes from the lab: miles use 1609.344 m (lab used 1.61 km/mile); duration rounds to the nearest second
(lab truncated, so it may differ by 1 s); the API request uses `profile=` (current Graphhopper parameter)
instead of the older `vehicle=`.

## Suggested Git workflow (if you set up GitHub)
`git init` → `.gitignore` is included → one branch per feature (`feature/react-ui`) → pull request →
teammate review → merge to `main`.

See `docs/BACKLOG.md` for future work.
