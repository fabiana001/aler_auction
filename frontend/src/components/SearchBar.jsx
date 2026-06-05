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
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
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
    <div ref={containerRef} style={{ position: "relative", flex: "1 1 auto", maxWidth: 400 }}>
      <div className="searchbar-wrap" style={{
        display: "flex",
        alignItems: "center",
        gap: 7,
        padding: "0 4px",
        height: 36,
        borderBottom: "2px solid transparent",
        transition: "border-color 0.15s",
      }}>
        <i className="ti ti-search" style={{ fontSize: 14, color: "var(--color-text-tertiary)", flexShrink: 0 }} />
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
            color: "var(--color-text-primary)",
            fontSize: 13,
            letterSpacing: "0.01em",
          }}
        />
        {loading && (
          <i className="ti ti-loader-2" style={{ fontSize: 13, color: "var(--color-text-tertiary)", animation: "spin 1s linear infinite", flexShrink: 0 }} />
        )}
        {!loading && query && (
          <button
            onClick={() => { setQuery(""); setResults([]); setShowDropdown(false); inputRef.current?.focus(); }}
            style={{
              background: "none", border: "none",
              color: "var(--color-text-tertiary)", cursor: "pointer",
              fontSize: 13, padding: 0, lineHeight: 1, display: "flex", flexShrink: 0,
            }}
          >
            <i className="ti ti-x" />
          </button>
        )}
      </div>

      {showDropdown && results.length > 0 && (
        <ul style={{
          position: "absolute",
          top: "calc(100% + 4px)",
          left: 0,
          right: 0,
          background: "#ffffff",
          border: "1px solid #e5e7eb",
          borderRadius: 5,
          listStyle: "none",
          margin: 0,
          padding: 4,
          zIndex: 9999,
          maxHeight: 320,
          overflowY: "auto",
          boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
        }}>
          {results.map((item, idx) => (
            <li
              key={item.id || idx}
              onMouseDown={(e) => { e.preventDefault(); handleSelect(item); }}
              onMouseEnter={() => setSelectedIndex(idx)}
              style={{
                padding: "7px 10px",
                cursor: "pointer",
                borderRadius: 4,
                background: idx === selectedIndex ? "#f9fafb" : "transparent",
                fontSize: 13,
              }}
            >
              <div style={{ fontWeight: 500, color: "#0f172a" }}>{getAddress(item)}</div>
              {getCity(item) && (
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 1 }}>{getCity(item)}</div>
              )}
            </li>
          ))}
        </ul>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .searchbar-wrap:focus-within { border-bottom-color: #2563EB !important; }
        .searchbar-wrap:focus-within i.ti-search { color: #2563EB !important; }
      `}</style>
    </div>
  );
}
