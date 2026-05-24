import { useState, useEffect } from "react";
import { fetchNearby } from "../utils/api";

const RADIUS_OPTIONS = [100, 250, 500, 1000, 2000];

function formatPrice(value) {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function NearbyPanel({ location, onClose }) {
  const [radius, setRadius] = useState(500);
  const [auctions, setAuctions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!location) return;
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchNearby(location.lat, location.lng, radius);
        if (!cancelled) {
          const items = Array.isArray(data) ? data : data.items || [];
          setAuctions(items);
        }
      } catch (err) {
        if (!cancelled) setError(err.message || "Failed to load nearby auctions");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [location, radius]);

  const count = auctions.length;
  const avgPricePerSqm =
    auctions.filter((a) => a.properties?.base_price_per_sqm || a.base_price_per_sqm).length > 0
      ? auctions
          .filter((a) => a.properties?.base_price_per_sqm || a.base_price_per_sqm)
          .reduce((sum, a) => sum + (a.properties?.base_price_per_sqm || a.base_price_per_sqm), 0) /
        auctions.filter((a) => a.properties?.base_price_per_sqm || a.base_price_per_sqm).length
      : null;
  const avgBasePrice =
    auctions.filter((a) => a.properties?.base_price_eur || a.base_price_eur).length > 0
      ? auctions
          .filter((a) => a.properties?.base_price_eur || a.base_price_eur)
          .reduce((sum, a) => sum + (a.properties?.base_price_eur || a.base_price_eur), 0) /
        auctions.filter((a) => a.properties?.base_price_eur || a.base_price_eur).length
      : null;

  function getDistance(a) {
    return a.distance != null ? `${Math.round(a.distance)}m` : a.properties?.distance ? `${Math.round(a.properties.distance)}m` : "";
  }

  function getAddress(a) {
    return a.properties?.address || a.address || "Indirizzo sconosciuto";
  }

  function getPrice(a) {
    return formatPrice(a.properties?.base_price_eur || a.base_price_eur);
  }

  function getType(a) {
    return a.properties?.property_type || a.property_type || "";
  }

  if (!location) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        bottom: 0,
        width: 340,
        background: "#1a1a2e",
        color: "#eee",
        zIndex: 2000,
        display: "flex",
        flexDirection: "column",
        boxShadow: "4px 0 24px rgba(0,0,0,0.5)",
        animation: "slideIn 0.25s ease-out",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <style>{`@keyframes slideIn { from { transform: translateX(-100%); } to { transform: translateX(0); } }`}</style>

      {/* Header */}
      <div style={{ padding: "14px 16px 10px", borderBottom: "1px solid #2a2a4a" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>
            Aste nel raggio di {radius >= 1000 ? `${radius / 1000}km` : `${radius}m`}
          </h2>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "#aaa", fontSize: 18, cursor: "pointer", padding: "2px 6px" }}
          >
            ✕
          </button>
        </div>

        {/* Radius selector */}
        <div style={{ display: "flex", gap: 4 }}>
          {RADIUS_OPTIONS.map((r) => (
            <button
              key={r}
              onClick={() => setRadius(r)}
              style={{
                flex: 1,
                padding: "4px 0",
                borderRadius: 6,
                border: "none",
                fontSize: 11,
                fontWeight: 600,
                cursor: "pointer",
                background: radius === r ? "#4a4aaa" : "#2a2a4a",
                color: radius === r ? "#fff" : "#aaa",
                fontFamily: "system-ui, sans-serif",
              }}
            >
              {r >= 1000 ? `${r / 1000}km` : `${r}m`}
            </button>
          ))}
        </div>
      </div>

      {/* Summary stats */}
      <div style={{ padding: "10px 16px", borderBottom: "1px solid #2a2a4a", display: "flex", gap: 16, fontSize: 12 }}>
        <div>
          <span style={{ opacity: 0.6 }}>Totale: </span>
          <strong>{count}</strong>
        </div>
        {avgPricePerSqm != null && (
          <div>
            <span style={{ opacity: 0.6 }}>€/m² medio: </span>
            <strong>{formatPrice(avgPricePerSqm)}</strong>
          </div>
        )}
        {avgBasePrice != null && (
          <div>
            <span style={{ opacity: 0.6 }}>Prezzo base medio: </span>
            <strong>{formatPrice(avgBasePrice)}</strong>
          </div>
        )}
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
        {loading && (
          <div style={{ padding: 20, textAlign: "center", opacity: 0.6, fontSize: 13 }}>Caricamento...</div>
        )}
        {error && (
          <div style={{ padding: 20, textAlign: "center", color: "#f66", fontSize: 13 }}>Errore: {error}</div>
        )}
        {!loading && !error && auctions.length === 0 && (
          <div style={{ padding: 20, textAlign: "center", opacity: 0.5, fontSize: 13 }}>Nessuna asta trovata</div>
        )}
        {auctions.map((a, idx) => (
          <div
            key={a.id || idx}
            style={{
              padding: "10px 16px",
              borderBottom: "1px solid #222244",
              cursor: "pointer",
              transition: "background 0.15s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "#222255")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 3 }}>{getAddress(a)}</div>
            <div style={{ display: "flex", gap: 10, fontSize: 11, opacity: 0.7 }}>
              {getDistance(a) && <span>📍 {getDistance(a)}</span>}
              <span>💰 {getPrice(a)}</span>
              {getType(a) && <span>🏠 {getType(a)}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
