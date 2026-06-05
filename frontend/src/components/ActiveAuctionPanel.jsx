import { useState } from "react";

const APE_COLORS = {
  A: "#16a34a", B: "#4ade80", C: "#86efac",
  D: "#facc15", E: "#fb923c", F: "#f87171", G: "#ef4444",
};

function formatPrice(val) {
  if (val == null) return "—";
  return new Intl.NumberFormat("it-IT", {
    style: "currency", currency: "EUR", maximumFractionDigits: 0,
  }).format(val);
}

function formatDate(iso) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function LotRow({ lot, onClick }) {
  const hasCoords = lot.lat != null && lot.lng != null;
  return (
    <tr
      style={{
        borderBottom: "0.5px solid var(--color-border-tertiary)", fontSize: 12,
        cursor: "pointer",
        transition: "background 0.12s",
      }}
      onClick={onClick}
      onMouseEnter={(e) => { e.currentTarget.style.background = "var(--color-background-secondary)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = ""; }}
    >
      <td style={{ padding: "6px 8px", color: "var(--color-text-secondary)", fontWeight: 500, whiteSpace: "nowrap" }}>
        {lot.lot_id}
      </td>
      <td style={{ padding: "6px 8px" }}>
        <span style={{ fontWeight: 500 }}>{lot.address}</span>
        {lot.street_number && <span style={{ color: "var(--color-text-tertiary)" }}> {lot.street_number}</span>}
        {lot.city && lot.city !== "MILANO" && (
          <span style={{ color: "var(--color-text-secondary)", marginLeft: 4, fontSize: 11 }}>{lot.city}</span>
        )}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "center" }}>
        <span style={{ color: "var(--color-text-secondary)" }}>{lot.rooms ?? "—"} loc</span>
        {lot.has_box && (
          <span style={{
            display: "inline-block", marginLeft: 5,
            background: "#eff6ff", color: "#1d4ed8",
            border: "0.5px solid #bfdbfe",
            borderRadius: 10, padding: "0 6px", fontSize: 10, fontWeight: 500,
          }}>+box</span>
        )}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "center", color: "var(--color-text-secondary)" }}>
        {lot.surface_sqm != null ? (
          <span>
            {lot.surface_sqm} m²
            {lot.has_box && lot.box_sqm != null && (
              <span style={{ color: "var(--color-text-tertiary)", fontSize: 10 }}> +{lot.box_sqm}</span>
            )}
          </span>
        ) : "—"}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "center" }}>
        {lot.ape_class ? (
          <span style={{
            background: APE_COLORS[lot.ape_class] || "#e2e8f0",
            color: ["A","B","C"].includes(lot.ape_class) ? "#fff" : "#1e293b",
            borderRadius: 4, padding: "1px 6px", fontWeight: 500, fontSize: 11,
          }}>
            {lot.ape_class}
          </span>
        ) : "—"}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 500, whiteSpace: "nowrap", color: "var(--color-text-primary)", fontFamily: "var(--font-mono)" }}>
        {formatPrice(lot.base_price_eur)}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "center", whiteSpace: "nowrap" }}>
        {lot.planimetria_url && (
          <a href={lot.planimetria_url} target="_blank" rel="noopener noreferrer"
            style={{ color: "#2563EB", marginRight: 4 }} title="Planimetria alloggio">
            <i className="ti ti-map-2" />
          </a>
        )}
        {lot.has_box && lot.box_planimetria_url && (
          <a href={lot.box_planimetria_url} target="_blank" rel="noopener noreferrer"
            style={{ color: "#1d4ed8", marginRight: 4 }} title="Planimetria box">
            <i className="ti ti-map-pin" />
          </a>
        )}
        {lot.foto_url && (
          <a href={lot.foto_url} target="_blank" rel="noopener noreferrer"
            style={{ color: "var(--color-text-secondary)" }} title="Foto">
            <i className="ti ti-photo" />
          </a>
        )}
      </td>
    </tr>
  );
}

export default function ActiveAuctionPanel({ data, onLotClick }) {
  const [dismissed, setDismissed] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [filter, setFilter] = useState("tutti");

  if (dismissed || !data || data.active_auctions?.length === 0) return null;

  const lots = data.lots || [];
  const withBox = lots.filter((l) => l.has_box);
  const displayLots = filter === "con_box" ? withBox : lots;

  const firstAuction = data.active_auctions?.[0];
  const deadline = firstAuction?.auction_date ? formatDate(firstAuction.auction_date) : null;

  const avgPsm = lots.length > 0
    ? lots.filter((l) => l.base_price_eur && l.surface_sqm)
        .reduce((s, l) => s + l.base_price_eur / l.surface_sqm, 0) /
      lots.filter((l) => l.base_price_eur && l.surface_sqm).length
    : null;

  return (
    <div style={{
      backgroundColor: "#ffffff",
      borderBottom: "0.5px solid var(--color-border-secondary)",
      borderLeft: "3px solid #2563EB",
      fontFamily: "var(--font-sans)",
    }}>
      {/* Header bar */}
      <div
        style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "8px 16px", cursor: "pointer",
        }}
        onClick={() => setExpanded((v) => !v)}
      >
        {/* Animated dot */}
        <span style={{
          width: 7, height: 7, borderRadius: "50%",
          background: "#22C55E", flexShrink: 0,
          animation: "pulse-dot 2s ease-in-out infinite",
          display: "inline-block",
        }} />
        <style>{`
          @keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        `}</style>

        <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.2 }}>
          <span style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)" }}>
            {firstAuction?.title || "Asta alloggi"}{deadline ? ` — ${deadline}` : ""}
          </span>
          <span style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>
            Prossima asta disponibile
          </span>
        </div>

        {/* Pills */}
        <div style={{ display: "flex", gap: 6, marginLeft: "auto" }}>
          <span style={{
            fontSize: 11, padding: "3px 9px", borderRadius: 20, border: "0.5px solid #BFDBFE",
            background: "#EFF6FF", color: "#1D4ED8",
          }}>
            {lots.length} alloggi
          </span>
          {withBox.length > 0 && (
            <span style={{
              fontSize: 11, padding: "3px 9px", borderRadius: 20, border: "0.5px solid #FED7AA",
              background: "#FFF7ED", color: "#C2410C",
            }}>
              {withBox.length} con box
            </span>
          )}
          {avgPsm != null && (
            <span style={{
              fontSize: 11, padding: "3px 9px", borderRadius: 20,
              border: "0.5px solid var(--color-border-secondary)",
              background: "var(--color-background-secondary)",
              color: "var(--color-text-secondary)",
            }}>
              {formatPrice(avgPsm)}/m²
            </span>
          )}
        </div>

        <button
          onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v); }}
          style={{
            backgroundColor: "#f9fafb",
            border: "0.5px solid #e5e7eb",
            color: "#4b5563", fontSize: 11,
            cursor: "pointer", padding: "3px 9px",
            borderRadius: 3, display: "flex", alignItems: "center", gap: 4,
            whiteSpace: "nowrap",
          }}
        >
          {expanded ? "▲ nascondi" : "mostra lotti"}
        </button>

        <button
          onClick={(e) => { e.stopPropagation(); setDismissed(true); }}
          style={{
            background: "none", border: "none", color: "var(--color-text-tertiary)",
            fontSize: 14, cursor: "pointer", padding: 0, lineHeight: 1,
            display: "flex", alignItems: "center",
          }}
          title="Chiudi"
        >
          <i className="ti ti-x" />
        </button>
      </div>

      {/* Expanded table */}
      {expanded && (
        <div style={{ borderTop: "0.5px solid var(--color-border-secondary)" }}>
          <div style={{
            display: "flex", gap: 0,
            backgroundColor: "#f9fafb",
            borderBottom: "0.5px solid var(--color-border-secondary)",
            padding: "6px 16px",
            alignItems: "center",
          }}>
            {[["tutti", `Tutti (${lots.length})`], ["con_box", `Con box (${withBox.length})`]].map(([f, label]) => (
              <button
                key={f}
                onClick={(e) => { e.stopPropagation(); setFilter(f); }}
                style={{
                  background: filter === f ? "#2563EB" : "#f9fafb",
                  color: filter === f ? "#fff" : "var(--color-text-secondary)",
                  border: "0.5px solid var(--color-border-secondary)",
                  borderRadius: f === "tutti" ? "4px 0 0 4px" : "0 4px 4px 0",
                  padding: "3px 12px", fontSize: 11, fontWeight: 500,
                  cursor: "pointer",
                }}
              >
                {label}
              </button>
            ))}
            {data.scraped_at && (
              <span style={{ marginLeft: "auto", fontSize: 10, color: "var(--color-text-tertiary)" }}>
                aggiornato {new Date(data.scraped_at).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" })}
              </span>
            )}
          </div>

          <div style={{ maxHeight: 320, overflowY: "auto", backgroundColor: "#ffffff" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ backgroundColor: "#f9fafb", borderBottom: "0.5px solid var(--color-border-secondary)" }}>
                  {["LOTTO", "INDIRIZZO", "LOCALI", "MQ", "APE", "PREZZO BASE", "DOC"].map((h, i) => (
                    <th key={h} style={{
                      padding: "5px 8px", fontSize: 10, fontWeight: 500,
                      color: "var(--color-text-tertiary)",
                      textAlign: i >= 2 && i <= 4 ? "center" : i === 5 ? "right" : i === 6 ? "center" : "left",
                      letterSpacing: "0.05em",
                      textTransform: "uppercase",
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {displayLots.map((lot) => (
                  <LotRow
                    key={lot.lot_id}
                    lot={lot}
                    onClick={() => {
                      onLotClick && onLotClick({
                        lat: lot.lat,
                        lng: lot.lng,
                        properties: {
                          address: `${lot.address} ${lot.street_number || ""}`.trim(),
                          city: lot.city,
                          surface_sqm: lot.surface_sqm,
                          base_price_eur: lot.base_price_eur,
                          property_type: lot.property_type,
                          lot_id: lot.lot_id,
                        },
                      });
                    }}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
