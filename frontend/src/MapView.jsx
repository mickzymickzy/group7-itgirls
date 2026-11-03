import { useEffect, useRef } from "react";
import L from "leaflet";

// Draws the route polyline and start/end markers on an OpenStreetMap map.
export default function MapView({ route }) {
  const el = useRef(null);
  const map = useRef(null);
  const layer = useRef(null);

  useEffect(() => {
    map.current = L.map(el.current).setView([20, 0], 2);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map.current);
    layer.current = L.layerGroup().addTo(map.current);
    return () => map.current.remove();
  }, []);

  useEffect(() => {
    if (!route) return;
    layer.current.clearLayers();
    L.polyline(route.coordinates, { color: "#fff", weight: 9, opacity: .9 }).addTo(layer.current);
    const line = L.polyline(route.coordinates, { color: "#EE5212", weight: 5 }).addTo(layer.current);
    const dot = (p, color, label) =>
      L.circleMarker(p, { radius: 8, color: "#fff", weight: 2, fillColor: color, fillOpacity: 1 })
        .bindTooltip(label).addTo(layer.current);
    dot([route.origin.lat, route.origin.lng], "#1D1B1A", route.origin.label);
    dot([route.destination.lat, route.destination.lng], "#EE5212", route.destination.label);
    map.current.fitBounds(line.getBounds(), { padding: [30, 30] });
  }, [route]);

  return <div ref={el} className="map" />;
}
