import { useState, useEffect } from "react";
import { fetchNearby } from "../utils/api";

const RADIUS_OPTIONS = [100, 250, 500, 1000, 2000];

function formatPrice(value) {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

function outcomeInfo(result) {
  if (!result) return { bg: "#fafafa", color: "#52525b", border: "#d4d4d8", label: "Esito non disp.", activeBg: "#71717a" };
  const r = result.toUpperCase();
  if (r === "AGGIUDICATA") return { bg: "#eff6ff", color: "#1d4ed8", border: "#bfdbfe", label: "Aggiudicata", activeBg: "#2563eb" };
  if (r.includes("DESERT")) return { bg: "#fff7ed", color: "#9a3412", border: "#fed7aa", label: "Asta deserta", activeBg: "#c2410c" };
  return { bg: "#fafafa", color: "#52525b", border: "#d4d4d8", label: result, activeBg: "#71717a" };
}

const OUTCOME_FILTERS = [
  { key: "tutte",       label: "Tutte",       activeBg: "#1d4ed8" },
  { key: "aggiudicate", label: "Aggiudicate", activeBg: "#2563eb" },
  { key: "deserte",     label: "Deserte",     activeBg: "#c2410c" },
];

export default function NearbyPanel({ location, onClose }) {
  const [radius, setRadius] = useState(500);
  const [auctions, setAuctions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("tutte");

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
        if (!cancelled) setError(err.message || "Errore");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [location, radius]);

  if (!location) return null;

  const getProp = (a, key) => a.properties?.[key] ?? a[key];

  const avgPsm = (() => {
    const vals = auctions.map((a) => getProp(a, "base_price_per_sqm")).filter((v) => v != null);
    return vals.length ? vals.reduce((s, v) => s + v, 0) / vals.length : null;
  })();

  const avgBase = (() => {
    const vals = auctions.map((a) => getProp(a, "base_price_eur")).filter((v) => v != null);
    return vals.length ? vals.reduce((s, v) => s + v, 0) / vals.length : null;
  })();

  const filteredAuctions = auctions.filter((a) => {
    const result = (getProp(a, "auction_result") || "").toUpperCase();
    if (filter === "aggiudicate") return result === "AGGIUDICATA";
    if (filter === "deserte") return result.includes("DESERT");
    return true;
  });

  const radiusLabel = radius >= 1000 ? `${radius / 1000} km` : `${radius} m`;

  return (
    <div style={{
      width: 360,
      flexShrink: 0,
      background: "var(--color-background-primary)",
      borderLeft: "1px solid #e2e8f0",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      animation: "slideInRight 0.22s ease-out",
      boxShadow: "var(--shadow-panel)",
    }}>
      <style>{`@keyframes slideInRight { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>

      {/* Header */}
      <div style={{ padding: "14px 16px 12px", borderBottom: "0.5px solid #e2e8f0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
          <i className="ti ti-map-pin" style={{ fontSize: 14, color: "var(--color-text-secondary)" }} />
          <span style={{ fontSize: 11, fontWeight: 500, color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", flex: 1 }}>
            Aste nel raggio
          </span>
          <button onClick={onClose} style={{
            background: "none", border: "none", cursor: "pointer",
            color: "var(--color-text-tertiary)", fontSize: 16, padding: 0, lineHeight: 1,
            display: "flex", alignItems: "center",
          }}>
            <i className="ti ti-x" />
          </button>
        </div>

        {/* Radius chips */}
        <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>
          {RADIUS_OPTIONS.map((r) => {
            const active = radius === r;
            return (
              <button
                key={r}
                onClick={() => setRadius(r)}
                style={{
                  flex: 1,
                  padding: "3px 0",
                  borderRadius: 3,
                  border: "0.5px solid " + (active ? "var(--color-border-info)" : "var(--color-border-secondary)"),
                  fontSize: 11,
                  fontWeight: 500,
                  cursor: "pointer",
                  background: active ? "var(--color-background-info)" : "transparent",
                  color: active ? "var(--color-text-info)" : "var(--color-text-secondary)",
                  transition: "background 0.1s",
                  letterSpacing: "0.02em",
                }}
              >
                {r >= 1000 ? `${r / 1000}km` : `${r}m`}
              </button>
            );
          })}
        </div>

        {/* KPIs */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
          {[
            { val: auctions.length, unit: "aste nel raggio" },
            { val: avgPsm != null ? `${Math.round(avgPsm).toLocaleString("it-IT")} €` : "—", unit: "€/m² medio" },
            { val: avgBase != null ? formatPrice(avgBase) : "—", unit: "prezzo base medio" },
          ].map(({ val, unit }) => (
            <div key={unit} style={{
              background: "var(--color-background-secondary)",
              borderRadius: "var(--border-radius-md)",
              padding: "8px 10px",
            }}>
              <div style={{ fontSize: 16, fontWeight: 500, color: "var(--color-text-primary)", lineHeight: 1.1, fontFamily: "var(--font-mono)", letterSpacing: "-0.02em" }}>{val}</div>
              <div style={{ fontSize: 9, color: "var(--color-text-tertiary)", marginTop: 3, textTransform: "uppercase", letterSpacing: "0.05em" }}>{unit}</div>
            </div>
          ))}
        </div>
      </div>

      {/* List header + filters */}
      <div style={{
        padding: "8px 16px 6px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "0.5px solid #e2e8f0",
      }}>
        <span style={{ fontSize: 11, fontWeight: 500, color: "var(--color-text-tertiary)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
          {filteredAuctions.length} aste
        </span>
        <div style={{ display: "flex", gap: 4 }}>
          {OUTCOME_FILTERS.map(({ key, label, activeBg }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              style={{
                fontSize: 11, fontWeight: 500,
                padding: "3px 10px", borderRadius: 3,
                border: "1px solid " + (filter === key ? activeBg : "#e5e7eb"),
                background: filter === key ? activeBg : "#f9fafb",
                color: filter === key ? "#fff" : "#4b5563",
                cursor: "pointer", transition: "all 0.12s",
                letterSpacing: "0.04em",
              }}
              onMouseEnter={(e) => { if (filter !== key) e.currentTarget.style.background = "#e5e7eb"; }}
              onMouseLeave={(e) => { if (filter !== key) e.currentTarget.style.background = "#f9fafb"; }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: "auto", padding: "4px 8px 8px" }}>
        {loading && (
          <div style={{ padding: 20, textAlign: "center", fontSize: 13, color: "var(--color-text-tertiary)" }}>
            <i className="ti ti-loader-2" style={{ marginRight: 6 }} />Caricamento...
          </div>
        )}
        {error && (
          <div style={{ padding: 16, fontSize: 13, color: "var(--color-text-danger)" }}>Errore: {error}</div>
        )}
        {!loading && !error && filteredAuctions.length === 0 && (
          <div style={{ padding: 20, textAlign: "center", fontSize: 13, color: "var(--color-text-tertiary)" }}>
            Nessuna asta trovata
          </div>
        )}
        {filteredAuctions.map((a, idx) => {
          const addr = getProp(a, "address") || "Indirizzo sconosciuto";
          const date = getProp(a, "auction_date");
          const type = getProp(a, "property_type");
          const surface = getProp(a, "surface_sqm");
          const basePrice = getProp(a, "base_price_eur");
          const finalPrice = getProp(a, "final_offer_eur");
          const psm = getProp(a, "base_price_per_sqm");
          const result = getProp(a, "auction_result");
          const dist = a.distance != null ? `${Math.round(a.distance)} m` : null;
          const info = outcomeInfo(result);

          return (
            <div key={a.id || idx}
              style={{
                padding: "9px 10px 9px 12px",
                borderRadius: "var(--border-radius-md)",
                cursor: "pointer",
                transition: "filter 0.1s",
                background: info.bg,
                border: "0.5px solid " + info.border,
                borderLeft: "3px solid " + info.activeBg,
                marginBottom: 4,
              }}
              onMouseEnter={(e) => { e.currentTarget.style.filter = "brightness(0.97)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.filter = "none"; }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 6, marginBottom: 4 }}>
                <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)", lineHeight: 1.3, flex: 1 }}>
                  {addr}
                </span>
                <span style={{
                  fontSize: 10, padding: "2px 7px", borderRadius: 3,
                  fontWeight: 600, whiteSpace: "nowrap",
                  background: info.activeBg, color: "#fff", letterSpacing: "0.03em",
                }}>
                  {info.label}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                {date && (
                  <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 11, color: info.color }}>
                    <i className="ti ti-calendar" style={{ fontSize: 11 }} />{date}
                  </span>
                )}
                {type && (
                  <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 11, color: "var(--color-text-secondary)" }}>
                    <i className="ti ti-building" style={{ fontSize: 11 }} />{type}
                  </span>
                )}
                {surface != null && (
                  <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 11, color: "var(--color-text-secondary)" }}>
                    <i className="ti ti-ruler" style={{ fontSize: 11 }} />{surface} m²
                  </span>
                )}
                {dist && (
                  <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 11, color: "var(--color-text-secondary)" }}>
                    <i className="ti ti-map-pin" style={{ fontSize: 11 }} />{dist}
                  </span>
                )}
              </div>
              {(basePrice != null || finalPrice != null) && (
                <div style={{ marginTop: 5, display: "flex", alignItems: "center", gap: 8 }}>
                  {basePrice != null && (
                    <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)", fontFamily: "var(--font-mono)" }}>
                      Base: {formatPrice(basePrice)}
                    </span>
                  )}
                  {psm != null && (
                    <>
                      <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>·</span>
                      <span style={{ fontSize: 11, color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>{Math.round(psm).toLocaleString("it-IT")} €/m²</span>
                    </>
                  )}
                  {finalPrice != null && finalPrice > 0 && (
                    <>
                      <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>·</span>
                      <span style={{ fontSize: 11, color: info.color, fontWeight: 500, fontFamily: "var(--font-mono)" }}>Agg.: {formatPrice(finalPrice)}</span>
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
