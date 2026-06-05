import { useState, useEffect } from "react";
import { fetchUpcoming } from "../utils/api";

function formatDate(isoDate) {
  if (!isoDate) return "";
  const [y, m, d] = isoDate.split("-");
  return `${d}/${m}/${y}`;
}

function outcomeStyle(result) {
  if (!result) return null;
  const r = result.toUpperCase();
  if (r === "AGGIUDICATA") return { bg: "var(--color-background-success)", color: "var(--color-text-success)" };
  if (r.includes("DESERT")) return { bg: "var(--color-background-warning)", color: "var(--color-text-warning)" };
  return { bg: "var(--color-background-danger)", color: "var(--color-text-danger)" };
}

export default function NewAuctionsBanner({ onPinClick }) {
  const [auctions, setAuctions] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    fetchUpcoming(365)
      .then((data) => setAuctions(data.items || []))
      .catch(() => {});
  }, []);

  if (dismissed || auctions.length === 0) return null;

  return (
    <div style={{
      background: "#eff6ff",
      borderBottom: "0.5px solid #bfdbfe",
      boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
      fontFamily: "var(--font-sans)",
    }}>
      {/* Collapsed bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          padding: "8px 16px",
          gap: 10,
          cursor: "pointer",
        }}
        onClick={() => setExpanded((v) => !v)}
      >
        <i className="ti ti-bell-ringing" style={{ fontSize: 14, color: "#1d4ed8" }} />
        <span style={{ fontSize: 12, fontWeight: 600, color: "#1d4ed8" }}>
          {auctions.length} aste recenti
        </span>
        <span style={{ fontSize: 12, color: "#475569" }}>
          negli ultimi 12 mesi
        </span>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "#64748b" }}>
          {expanded ? "▲ nascondi" : "▼ mostra"}
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); setDismissed(true); }}
          style={{
            background: "none", border: "none",
            color: "#64748b", fontSize: 14,
            cursor: "pointer", padding: 0, lineHeight: 1,
            display: "flex", alignItems: "center",
          }}
          title="Chiudi"
        >
          <i className="ti ti-x" />
        </button>
      </div>

      {/* Expanded list */}
      {expanded && (
        <div style={{
          borderTop: "0.5px solid #bfdbfe",
          maxHeight: 240,
          overflowY: "auto",
          background: "#f8fafc",
        }}>
          {auctions.map((a) => {
            const style = outcomeStyle(a.properties?.auction_result);
            return (
              <div
                key={a.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "7px 16px",
                  cursor: "pointer",
                  borderBottom: "0.5px solid #dbeafe",
                  transition: "background 0.12s",
                  fontSize: 12,
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "var(--color-background-secondary)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                onClick={() => { onPinClick && onPinClick(a); setExpanded(false); }}
              >
                <span style={{ color: "var(--color-text-secondary)", fontWeight: 500, minWidth: 72, fontSize: 11, fontFamily: "var(--font-mono)" }}>
                  {formatDate(a.parsed_date)}
                </span>
                <span style={{ flex: 1, color: "var(--color-text-primary)" }}>
                  {a.properties?.address || "Indirizzo sconosciuto"}
                </span>
                <span style={{ color: "var(--color-text-tertiary)", fontSize: 11, whiteSpace: "nowrap" }}>
                  {a.properties?.property_type || ""}
                </span>
                {a.properties?.base_price_eur != null && (
                  <span style={{ color: "var(--color-text-secondary)", fontWeight: 500, fontSize: 11, whiteSpace: "nowrap", fontFamily: "var(--font-mono)" }}>
                    {new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(a.properties.base_price_eur)}
                  </span>
                )}
                {a.properties?.auction_result && style && (
                  <span style={{
                    padding: "2px 7px", borderRadius: 3, fontSize: 10, fontWeight: 500, letterSpacing: "0.03em",
                    background: style.bg, color: style.color, whiteSpace: "nowrap",
                  }}>
                    {a.properties.auction_result === "AGGIUDICATA" ? "Aggiudicata" : a.properties.auction_result}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
