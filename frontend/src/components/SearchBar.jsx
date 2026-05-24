import { useState, useRef, useEffect } from "react";

export default function SearchBar({ onSelect }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const containerRef = useRef(null);
  const inputRef = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length < 2) {
      setResults([]);
      setShowDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const resp = await fetch(
          `${import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"}/api/auctions/search?q=${encodeURIComponent(query)}`
        );
        const data = await resp.json();
        const items = Array.isArray(data) ? data : data.items || [];
        setResults(items.slice(0, 10));
        setShowDropdown(true);
        setSelectedIndex(-1);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  function handleSelect(item) {
    const lat = item.lat ?? item.geometry?.coordinates?.[1];
    const lng = item.lng ?? item.geometry?.coordinates?.[0];
    const address = item.properties?.address || item.address || "";
    setQuery(address);
    setShowDropdown(false);
    onSelect({ lat, lng, item });
  }

  function handleKeyDown(e) {
    if (!showDropdown || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, -1));
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault();
      handleSelect(results[selectedIndex]);
    } else if (e.key === "Escape") {
      setShowDropdown(false);
    }
  }

  function getAddress(item) {
    return item.properties?.address || item.address || "Indirizzo sconosciuto";
  }

  function getCity(item) {
    return item.properties?.city || item.city || "";
  }

  return (
    <div ref={containerRef} style={{ position: "relative", flex: "1 1 auto", maxWidth: 420 }}>
      <div style={{ display: "flex", alignItems: "center", background: "#16213e", borderRadius: 8, border: "1px solid #2a2a4a", padding: "0 10px", height: 38 }}>
        <span style={{ marginRight: 6, fontSize: 14, opacity: 0.7 }}>🔍</span>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => { if (results.length > 0) setShowDropdown(true); }}
          onKeyDown={handleKeyDown}
          placeholder="Cerca per via o indirizzo..."
          style={{
            flex: 1,
            background: "transparent",
            border: "none",
            outline: "none",
            color: "#fff",
            fontSize: 14,
            height: "100%",
            fontFamily: "system-ui, sans-serif",
          }}
        />
        {loading && (
          <span style={{ fontSize: 14, animation: "spin 1s linear infinite", display: "inline-block" }}>⏳</span>
        )}
        {!loading && query && (
          <button
            onClick={() => { setQuery(""); setResults([]); setShowDropdown(false); inputRef.current?.focus(); }}
            style={{ background: "none", border: "none", color: "#aaa", cursor: "pointer", fontSize: 16, padding: "0 2px" }}
          >
            ✕
          </button>
        )}
      </div>

      {showDropdown && results.length > 0 && (
        <ul
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            background: "#16213e",
            border: "1px solid #2a2a4a",
            borderRadius: 8,
            listStyle: "none",
            margin: 0,
            padding: 4,
            zIndex: 9999,
            maxHeight: 320,
            overflowY: "auto",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
          }}
        >
          {results.map((item, idx) => (
            <li
              key={item.id || idx}
              onMouseDown={(e) => { e.preventDefault(); handleSelect(item); }}
              onMouseEnter={() => setSelectedIndex(idx)}
              style={{
                padding: "8px 12px",
                cursor: "pointer",
                borderRadius: 6,
                background: idx === selectedIndex ? "#2a2a5a" : "transparent",
                color: "#eee",
                fontSize: 13,
                fontFamily: "system-ui, sans-serif",
              }}
            >
              <div style={{ fontWeight: 600 }}>{getAddress(item)}</div>
              {getCity(item) && (
                <div style={{ fontSize: 11, opacity: 0.6, marginTop: 2 }}>{getCity(item)}</div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
