/*
 * PlaceInput.jsx - text box with an autocomplete dropdown.
 * - waits 350 ms after you stop typing, then asks the backend for suggestions
 * - arrow keys + Enter, or a click, picks a suggestion
 * - `value` = { text, place }. `place` is set only after a suggestion is picked;
 *   typing again clears it (so we never send stale coordinates).
 */
import { useEffect, useRef, useState } from "react";
import { getSuggestions } from "./api.js";
import Icon from "./icons.jsx";

export default function PlaceInput({ label, dot, placeholder, value, onChange }) {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [busy, setBusy] = useState(false);
  const timer = useRef(null);
  const ctrl = useRef(null);

  // Look up suggestions whenever the typed text changes (and no place is picked yet)
  useEffect(() => {
    clearTimeout(timer.current);
    ctrl.current?.abort();
    if (value.place || value.text.trim().length < 3) { setItems([]); setBusy(false); return; }
    setBusy(true);
    timer.current = setTimeout(async () => {
      ctrl.current = new AbortController();
      try {
        const list = await getSuggestions(value.text.trim(), ctrl.current.signal);
        setItems(list); setActive(-1); setOpen(true); setBusy(false);
      } catch (e) { if (e.name !== "AbortError") setBusy(false); }
    }, 350);
    return () => clearTimeout(timer.current);
  }, [value.text, value.place]);

  const pick = p => { onChange({ text: p.label, place: p }); setOpen(false); setItems([]); };

  function onKey(e) {
    if (!open || !items.length) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setActive(a => (a + 1) % items.length); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive(a => (a <= 0 ? items.length - 1 : a - 1)); }
    else if (e.key === "Enter" && active >= 0) { e.preventDefault(); pick(items[active]); }
    else if (e.key === "Escape") setOpen(false);
  }

  return (
    <div className="field">
      <span className="field-label">{label}</span>
      <div className="input-wrap">
        <i className={"pin " + dot} />
        <input
          value={value.text}
          placeholder={placeholder}
          onChange={e => onChange({ text: e.target.value, place: null })}
          onFocus={() => items.length && setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
          onKeyDown={onKey}
          autoComplete="off"
          role="combobox"
          aria-expanded={open}
        />
        {busy && <span className="spinner" aria-hidden="true" />}
        {value.place && <span className="tick" title="Place selected"><Icon name="check" size={16} /></span>}
      </div>
      {open && items.length > 0 && (
        <ul className="suggest" role="listbox">
          {items.map((p, i) => (
            <li key={i} role="option" className={i === active ? "on" : ""}
                onMouseDown={() => pick(p)} onMouseEnter={() => setActive(i)}>
              <span className="s-icon"><Icon name="pin" size={16} /></span>
              <span><b>{p.label.split(",")[0]}</b><small>{p.label.split(",").slice(1).join(",").trim() || p.kind}</small></span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
