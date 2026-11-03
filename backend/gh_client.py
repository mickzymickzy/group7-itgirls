"""
gh_client.py - Graphhopper API client + formatting helpers.

This is the "engine" of the project. It is the lab's code (geocoding(),
routing, unit conversion, hh:mm:ss formatting, error handling) refactored into
reusable functions so BOTH the web API (app.py) and the terminal app (cli.py)
share one implementation.

Special key: set GRAPHHOPPER_KEY=demo to use built-in sample data (no network),
handy for demos and tests.
"""
import urllib.parse
import requests

GEOCODE_URL = "https://graphhopper.com/api/1/geocode?"
ROUTE_URL = "https://graphhopper.com/api/1/route?"
PROFILES = ["car", "bike", "foot"]          # profiles on Graphhopper's free plan
METERS_PER_MILE = 1609.344                   # lab used 1000*1.61 (~0.2% off)
TIMEOUT = 15

# Graphhopper "sign" codes -> maneuver names the frontend maps to arrows.
SIGNS = {-98: "uturn", -8: "uturn", -7: "keep_left", -3: "sharp_left",
         -2: "left", -1: "slight_left", 0: "straight", 1: "slight_right",
         2: "right", 3: "sharp_right", 4: "arrive", 5: "via",
         6: "roundabout", 7: "keep_right"}


class GraphhopperError(Exception):
    """Raised for any failure; carries an HTTP-like status and a user message."""
    def __init__(self, message, status=502):
        super().__init__(message)
        self.message, self.status = message, status


# ---------- formatting helpers (lab Part 5 steps 2-6) ----------
def meters_to_km(m):
    return m / 1000.0


def meters_to_miles(m):
    return m / METERS_PER_MILE


def format_duration(ms):
    """Milliseconds -> 'hh:mm:ss' (the lab's modulo trick, done with divmod)."""
    total = int(round(ms / 1000.0))
    hrs, rem = divmod(total, 3600)
    mins, secs = divmod(rem, 60)
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


# ---------- API calls ----------
def _get_json(url):
    try:
        r = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise GraphhopperError(f"Could not reach Graphhopper: {e}", 503)
    try:
        data = r.json()
    except ValueError:
        raise GraphhopperError("Graphhopper returned an unreadable response.", 502)
    return r.status_code, data


def _hit_to_place(h):
    """Turn one Graphhopper geocode 'hit' into our simple place dict."""
    parts = [h.get("name"), h.get("state"), h.get("country")]
    label = ", ".join(p for p in parts if p)    # lab's new_loc logic, simplified
    return {"lat": h["point"]["lat"], "lng": h["point"]["lng"],
            "label": label or h.get("name", ""), "kind": h.get("osm_value", "")}


def _search(query, key, limit):
    url = GEOCODE_URL + urllib.parse.urlencode({"q": query, "limit": str(limit), "key": key})
    status, data = _get_json(url)
    if status != 200:
        raise GraphhopperError(data.get("message", f"Geocoding failed ({status})"), status)
    return [_hit_to_place(h) for h in data.get("hits", []) if "point" in h]


def geocode(location, key):
    """Lab 'geocoding()' function. Accepts text OR a place the user already picked
    from the autocomplete list ({"lat","lng","label"}), which skips the lookup."""
    if isinstance(location, dict):
        try:
            return {"lat": float(location["lat"]), "lng": float(location["lng"]),
                    "label": str(location.get("label", "")), "kind": location.get("kind", "")}
        except (KeyError, TypeError, ValueError):
            raise GraphhopperError("Invalid place.", 400)
    location = (location or "").strip()
    if not location:
        raise GraphhopperError("Please enter a location.", 400)
    if key == "demo":
        return _demo_geocode(location)
    places = _search(location, key, 1)          # lab step 14: empty 'hits' list
    if not places:
        raise GraphhopperError(f"No match found for '{location}'.", 404)
    return places[0]


def suggest(query, key, limit=5):
    """Autocomplete: up to `limit` matching places for what the user has typed so far."""
    query = (query or "").strip()
    if len(query) < 3:
        return []
    if key == "demo":
        return [{"lat": lat, "lng": lng, "label": label, "kind": "city"}
                for k, (label, lat, lng) in _DEMO_PLACES.items() if query.lower() in label.lower()]
    return _search(query, key, limit)


def route(orig, dest, key, profile="car"):
    """Lab Part 5 routing. Returns a parsed dict (units are raw meters / ms)."""
    if profile not in PROFILES:
        raise GraphhopperError(f"Unknown vehicle profile '{profile}'.", 400)
    if key == "demo":
        return _demo_route(orig, dest, profile)
    q = urllib.parse.urlencode({"key": key, "profile": profile,
                                "points_encoded": "false", "instructions": "true"})
    pts = f"&point={orig['lat']}%2C{orig['lng']}&point={dest['lat']}%2C{dest['lng']}"
    status, data = _get_json(ROUTE_URL + q + pts)
    if status != 200:
        raise GraphhopperError(data.get("message", f"Routing failed ({status})"), status)
    p = data["paths"][0]
    return {
        "distance_m": p["distance"], "time_ms": p["time"],
        "ascend_m": p.get("ascend"), "descend_m": p.get("descend"),
        # GeoJSON is [lng, lat]; Leaflet wants [lat, lng]
        "coordinates": [[c[1], c[0]] for c in p["points"]["coordinates"]],
        "instructions": [{"text": i["text"], "distance_m": i["distance"],
                          "time_ms": i["time"], "sign": SIGNS.get(i.get("sign", 0), "straight"),
                          "street": i.get("street_name", "")} for i in p.get("instructions", [])],
    }


def add_units(r):
    """Attach km, miles and hh:mm:ss so the UI can switch units with no refetch."""
    r["distance_km"] = round(meters_to_km(r["distance_m"]), 2)
    r["distance_mi"] = round(meters_to_miles(r["distance_m"]), 2)
    r["duration"] = format_duration(r["time_ms"])
    for i in r["instructions"]:
        i["distance_km"] = round(meters_to_km(i["distance_m"]), 2)
        i["distance_mi"] = round(meters_to_miles(i["distance_m"]), 2)
        i["duration"] = format_duration(i["time_ms"])
    return r


def get_directions(start, end, key, profile="car"):
    """One call that does the whole lab flow: geocode x2 -> route -> format."""
    o, d = geocode(start, key), geocode(end, key)
    res = add_units(route(o, d, key, profile))
    res.update({"origin": o, "destination": d, "profile": profile})
    return res


# ---------- demo data (GRAPHHOPPER_KEY=demo) ----------
_DEMO_PLACES = {
    "washington": ("Washington, District of Columbia, United States", 38.8950368, -77.0365427),
    "baltimore": ("Baltimore, Maryland, United States", 39.2908816, -76.610759),
}


def _demo_geocode(q):
    for k, (label, lat, lng) in _DEMO_PLACES.items():
        if k in q.lower():
            return {"lat": lat, "lng": lng, "label": label, "kind": "city"}
    raise GraphhopperError(f"Demo mode only knows Washington and Baltimore (got '{q}').", 404)


def _demo_route(o, d, profile):
    speed = {"car": 1.0, "bike": 3.2, "foot": 11.0}[profile]
    steps = [("Continue onto 15th Street Northwest", 424.3, "straight"),
             ("Turn right onto New York Avenue Northwest", 912.0, "right"),
             ("Turn slight right onto K Street Northwest", 200.0, "slight_right"),
             ("Turn left onto 7th Street Northwest", 100.0, "left"),
             ("Turn right onto New York Avenue Northwest", 7600.0, "right"),
             ("Keep left onto Baltimore-Washington Parkway", 51600.0, "keep_left"),
             ("Turn right onto West Baltimore Street", 600.0, "right"),
             ("Turn left onto North Charles Street", 200.0, "left"),
             ("Arrive at destination", 0.0, "arrive")]
    total = sum(s[1] for s in steps)
    ms = 3089865 * speed
    return {"distance_m": total, "time_ms": ms, "ascend_m": 713.5, "descend_m": 690.0,
            "coordinates": [[o["lat"], o["lng"]], [38.99, -76.93], [d["lat"], d["lng"]]],
            "instructions": [{"text": t, "distance_m": m, "time_ms": ms * m / total,
                              "sign": s, "street": ""} for t, m, s in steps]}
