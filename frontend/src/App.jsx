
import { useState } from "react";
import { getDirections } from "./api.js";
import MapView from "./MapView.jsx";
import PlaceInput from "./PlaceInput.jsx";
import Icon from "./icons.jsx";

const PROFILES = [
  { id: "car", label: "Car", icon: "car" },
  { id: "bike", label: "Bike", icon: "bike" },
  { id: "foot", label: "Walk", icon: "foot" },
];
const UNITS = [["both", "Both"], ["imperial", "Miles"], ["metric", "Km"]];
const TURN = {
  straight: ["up", 0], slight_right: ["up", 45], keep_right: ["up", 45], right: ["up", 90], sharp_right: ["up", 135],
  slight_left: ["up", -45], keep_left: ["up", -45], left: ["up", -90], sharp_left: ["up", -135],
  uturn: ["uturn", 0], roundabout: ["loop", 0], arrive: ["flag", 0], via: ["dot", 0],
};

const fmt = (o, units, d = 1) =>
  units === "metric" ? `${o.km.toFixed(d)} km`
  : units === "imperial" ? `${o.mi.toFixed(d)} mi`
  : `${o.mi.toFixed(d)} mi / ${o.km.toFixed(d)} km`;

function loadHistory() {
  try {
    const h = JSON.parse(localStorage.getItem("history2") || "[]");
    return Array.isArray(h) ? h : [];
  } catch { return []; }
}

export default function App() {
  const empty = { text: "", place: null };
  const [start, setStart] = useState(empty);
  const [end, setEnd] = useState(empty);
  const [profile, setProfile] = useState("car");
  const [units, setUnits] = useState("both");
  const [route, setRoute] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState(loadHistory);

  async function search(s = start, e = end, p = profile) {
    setError(""); setLoading(true);
    try {
      // send the picked place (exact coordinates) if there is one, otherwise the typed text
      const r = await getDirections(s.place || s.text, e.place || e.text, p);
      setRoute(r);
      const entry = { start: s, end: e, profile: p };
      const same = h => h.start.text === s.text && h.end.text === e.text && h.profile === p;
      const next = [entry, ...history.filter(h => !same(h))].slice(0, 5);
      setHistory(next);
      try { localStorage.setItem("history2", JSON.stringify(next)); } catch {}
    } catch (err) {
      setError(err.message);
    } finally { setLoading(false); }
  }

  const swap = () => { setStart(end); setEnd(start); };
  const pick = h => { setStart(h.start); setEnd(h.end); setProfile(h.profile); search(h.start, h.end, h.profile); };

  return (
    <div className="app">
      <header className="top">
        <div className="top-in"><img src="/logo.png" alt="logo" height="44" /><h1>AutoAssist</h1></div>
      </header>

      <div className="layout">
        <aside className="panel">
          <h2 className="panel-title">Plan a route</h2>
          <p className="panel-sub">Choose a start, a destination and how you are travelling.</p>
          <form onSubmit={ev => { ev.preventDefault(); search(); }}>
            <PlaceInput label="From" dot="start" placeholder="Search a city or place"
                        value={start} onChange={setStart} />
            <button type="button" className="swap" onClick={swap} title="Swap places" aria-label="Swap places"><Icon name="swap" size={16} /></button>
            <PlaceInput label="To" dot="end" placeholder="Search a city or place"
                        value={end} onChange={setEnd} />

            <span className="field-label">Travel by</span>
            <div className="seg" role="group" aria-label="Vehicle">
              {PROFILES.map(p => (
                <button type="button" key={p.id} className={profile === p.id ? "on" : ""} onClick={() => setProfile(p.id)}>
                  <Icon name={p.icon} size={22} />{p.label}
                </button>
              ))}
            </div>
            <button className="go" disabled={loading || !start.text.trim() || !end.text.trim()}>
              {loading ? "Finding route…" : "Get directions"}
            </button>
          </form>

          {error && <div className="error" role="alert"><Icon name="alert" size={18} /><span>{error}</span></div>}

          {history.length > 0 && (
            <div className="history">
              <div className="history-head"><h3>Recent trips</h3>
                <button className="link" onClick={() => { setHistory([]); try { localStorage.removeItem("history2"); } catch {} }}>Clear</button>
              </div>
              {history.map((h, i) => (
                <button key={i} onClick={() => pick(h)}>
                  <Icon name={PROFILES.find(p => p.id === h.profile)?.icon} size={16} />
                  <span className="h-text">{h.start.text.split(",")[0]} to {h.end.text.split(",")[0]}</span>
                </button>
              ))}
            </div>
          )}
        </aside>

        <main>
          <div className="map-card"><MapView route={route} />
            {!route && <div className="map-hint">Search two places to see your route</div>}
          </div>
          {route && (
            <section className="result">
              <div className="result-head">
                <h2>{route.origin.label.split(",")[0]}<span className="to">to</span>{route.destination.label.split(",")[0]}</h2>
                <div className="seg small">
                  {UNITS.map(([id, l]) => <button key={id} className={units === id ? "on" : ""} onClick={() => setUnits(id)}>{l}</button>)}
                </div>
              </div>
              <div className="stats">
                <div><span>Distance</span><b>{fmt({ km: route.distance_km, mi: route.distance_mi }, units)}</b></div>
                <div><span>Duration</span><b>{route.duration}</b></div>
                {route.ascend_m != null && <div><span>Climb / descent</span><b>{Math.round(route.ascend_m)} m / {Math.round(route.descend_m)} m</b></div>}
              </div>
              <table>
                <thead><tr><th></th><th>Instruction</th><th>Distance</th><th>Time</th></tr></thead>
                <tbody>
                  {route.instructions.map((i, n) => (
                    <tr key={n}>
                      <td className="arrow">{(t => <Icon name={t[0]} rotate={t[1]} />)(TURN[i.sign] || TURN.straight)}</td>
                      <td>{i.text}</td>
                      <td>{fmt({ km: i.distance_km, mi: i.distance_mi }, units, 2)}</td>
                      <td className="mut">{i.duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </main>
      </div>
      <footer>Route data © OpenStreetMap contributors. Directions by Graphhopper.</footer>
    </div>
  );
}
