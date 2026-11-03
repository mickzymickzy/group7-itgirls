// api.js - the ONLY place the frontend talks to the Python backend.

// Directions. `start` / `end` can be text, or a place picked from autocomplete.
export async function getDirections(start, end, profile) {
  const res = await fetch("/api/directions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ start, end, profile }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

// Autocomplete suggestions for what the user has typed so far.
export async function getSuggestions(q, signal) {
  const res = await fetch(`/api/suggest?q=${encodeURIComponent(q)}`, { signal });
  const data = await res.json().catch(() => ({}));
  return data.suggestions || [];
}
