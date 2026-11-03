"""
app.py - Flask web API (+ serves the built React app).

Endpoints
  GET  /api/health      -> {"ok": true, "mode": "live"|"demo"}
  GET  /api/profiles    -> {"profiles": ["car","bike","foot"]}
  GET  /api/suggest?q=  -> autocomplete suggestions
  POST /api/directions  -> body {"start","end","profile"}; returns directions JSON

Run:  GRAPHHOPPER_KEY=your_key python app.py     (then open http://localhost:5000)
"""
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import gh_client as gh


def load_env_file():
    """Read KEY=value lines from backend/.env (or the folder above it) into os.environ.
    Written by hand so no extra package (python-dotenv) is needed."""
    here = os.path.dirname(os.path.abspath(__file__))
    for folder in (here, os.path.dirname(here)):
        try:
            with open(os.path.join(folder, ".env"), encoding="utf-8-sig") as f:
                lines = f.read().splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if not os.environ.get(k.strip()):
                os.environ[k.strip()] = v.strip().strip('"').strip("'")
        return


load_env_file()
DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
app = Flask(__name__, static_folder=None)
CORS(app)   # lets the Vite dev server (port 5173) call this API (port 5000)


def api_key():
    return os.environ.get("GRAPHHOPPER_KEY", "").strip()


@app.get("/api/health")
def health():
    k = api_key()
    return jsonify(ok=bool(k), mode="demo" if k == "demo" else "live")


@app.get("/api/profiles")
def profiles():
    return jsonify(profiles=gh.PROFILES)


@app.get("/api/suggest")
def suggest():
    """Autocomplete: /api/suggest?q=man -> {"suggestions": [{label, lat, lng, kind}, ...]}"""
    key = api_key()
    if not key:
        return jsonify(suggestions=[], error="Server has no GRAPHHOPPER_KEY set."), 500
    try:
        return jsonify(suggestions=gh.suggest(request.args.get("q", ""), key))
    except gh.GraphhopperError as e:
        return jsonify(suggestions=[], error=e.message), e.status


@app.post("/api/directions")
def directions():
    key = api_key()
    if not key:
        return jsonify(error="Server has no GRAPHHOPPER_KEY set."), 500
    body = request.get_json(silent=True) or {}
    try:
        return jsonify(gh.get_directions(body.get("start"), body.get("end"),
                                         key, body.get("profile", "car")))
    except gh.GraphhopperError as e:
        return jsonify(error=e.message), e.status


# Serve the compiled React app (npm run build) from the same server.
@app.get("/", defaults={"path": ""})
@app.get("/<path:path>")
def frontend(path):
    if os.path.isdir(DIST):
        full = os.path.join(DIST, path)
        if path and os.path.isfile(full):
            return send_from_directory(DIST, path)
        return send_from_directory(DIST, "index.html")
    return jsonify(message="API running. Build the frontend (npm run build) or use npm run dev."), 200


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
