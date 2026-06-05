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
        borderBottom: "0.5px solid #e2e8f0", fontSize: 12,
        cursor: hasCoords ? "pointer" : "default",
      }}
      onClick={hasCoords ? onClick : undefined}
      onMouseEnter={(e) => { if (hasCoords) e.currentTarget.style.background = "#fef9c3"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = ""; }}
    >
      <td style={{ padding: "6px 8px", color: "#64748b", fontWeight: 600, whiteSpace: "nowrap" }}>
        {lot.lot_id}
      </td>
      <td style={{ padding: "6px 8px" }}>
        <span style={{ fontWeight: 500 }}>{lot.address}</span>
        {lot.street_number && <span style={{ color: "#94a3b8" }}> {lot.street_number}</span>}
        {lot.city && lot.city !== "MILANO" && (
          <span style={{ color: "#64748b", marginLeft: 4, fontSize: 11 }}>{lot.city}</span>
        )}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "center" }}>
        <span style={{ color: "#475569" }}>{lot.rooms ?? "—"} loc</span>
        {lot.has_box && (
          <span style={{
            display: "inline-block", marginLeft: 5,
            background: "#eff6ff", color: "#1d4ed8",
            border: "1px solid #bfdbfe",
            borderRadius: 10, padding: "0 6px", fontSize: 10, fontWeight: 600,
          }}>+box</span>
        )}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "center", color: "#475569" }}>
        {lot.surface_sqm != null ? (
          <span>
            {lot.surface_sqm} m²
            {lot.has_box && lot.box_sqm != null && (
              <span style={{ color: "#94a3b8", fontSize: 10 }}> +{lot.box_sqm}</span>
            )}
          </span>
        ) : "—"}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "center" }}>
        {lot.ape_class ? (
          <span style={{
            background: APE_COLORS[lot.ape_class] || "#e2e8f0",
            color: ["A","B","C"].includes(lot.ape_class) ? "#fff" : "#1e293b",
            borderRadius: 4, padding: "1px 6px", fontWeight: 700, fontSize: 11,
          }}>
            {lot.ape_class}
          </span>
        ) : "—"}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 600, whiteSpace: "nowrap", color: "#0f172a", fontFamily: "'IBM Plex Mono', monospace" }}>
        {formatPrice(lot.base_price_eur)}
      </td>
      <td style={{ padding: "6px 8px", textAlign: "center", whiteSpace: "nowrap" }}>
        {lot.planimetria_url && (
          <a href={lot.planimetria_url} target="_blank" rel="noopener noreferrer"
            style={{ color: "#3b82f6", marginRight: 4 }} title="Planimetria alloggio">
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
            style={{ color: "#64748b" }} title="Foto">
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
  const [filter, setFilter] = useState("tutti"); // "tutti" | "con_box"

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
      background: "linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%)",
      borderBottom: "2px solid #f59e0b",
      boxShadow: "0 4px 16px rgba(245,158,11,0.18)",
      fontFamily: "var(--font-sans)",
    }}>
      {/* Header bar */}
      <div
        style={{
          display: "flex", alignItems: "center", gap: 10,
          padding: "9px 16px", cursor: "pointer",
        }}
        onClick={() => setExpanded((v) => !v)}
      >
        <i className="ti ti-gavel" style={{ fontSize: 14, color: "#92400e" }} />
        <span style={{ fontSize: 12, fontWeight: 700, color: "#92400e", letterSpacing: "0.07em" }}>
          ASTA ATTIVA
        </span>
        <span style={{ fontSize: 12, fontWeight: 600, color: "#1e293b" }}>
          {firstAuction?.title || "Asta Alloggi"}
        </span>
        {deadline && (
          <span style={{
            background: "#fef3c7", border: "1px solid #f59e0b",
            borderRadius: 12, padding: "1px 9px",
            fontSize: 11, fontWeight: 600, color: "#92400e",
          }}>
            <i className="ti ti-calendar" style={{ marginRight: 3 }} />
            {deadline}
          </span>
        )}
        <span style={{
          marginLeft: 6,
          background: "#f59e0b", color: "#fff",
          borderRadius: 3, padding: "1px 9px",
          fontSize: 11, fontWeight: 700, letterSpacing: "0.03em",
        }}>
          {lots.length} alloggi
        </span>
        {withBox.length > 0 && (
          <span style={{
            background: "#eff6ff", color: "#1d4ed8",
            border: "1px solid #bfdbfe",
            borderRadius: 12, padding: "1px 9px",
            fontSize: 11, fontWeight: 600,
          }}>
            {withBox.length} con box
          </span>
        )}
        {avgPsm != null && (
          <span style={{ fontSize: 11, color: "#64748b", marginLeft: 4 }}>
            avg {formatPrice(avgPsm)}/m²
          </span>
        )}
        <span style={{ marginLeft: "auto", fontSize: 11, color: "#78350f" }}>
          {expanded ? "▲ nascondi" : "▼ mostra lotti"}
        </span>
        <button
          onClick={(e) => { e.stopPropagation(); setDismissed(true); }}
          style={{
            background: "none", border: "none", color: "#78350f",
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
        <div style={{ borderTop: "1px solid #f59e0b" }}>
          {/* Filter tabs */}
          <div style={{
            display: "flex", gap: 0,
            background: "#fffbeb",
            borderBottom: "0.5px solid #fde68a",
            padding: "6px 16px",
            alignItems: "center",
          }}>
            {[["tutti", `Tutti (${lots.length})`], ["con_box", `Con box (${withBox.length})`]].map(([f, label]) => (
              <button
                key={f}
                onClick={(e) => { e.stopPropagation(); setFilter(f); }}
                style={{
                  background: filter === f ? "#f59e0b" : "transparent",
                  color: filter === f ? "#fff" : "#78350f",
                  border: "1px solid #f59e0b",
                  borderRadius: f === "tutti" ? "4px 0 0 4px" : "0 4px 4px 0",
                  padding: "3px 12px", fontSize: 11, fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                {label}
              </button>
            ))}
            {data.scraped_at && (
              <span style={{ marginLeft: "auto", fontSize: 10, color: "#a16207" }}>
                aggiornato {new Date(data.scraped_at).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" })}
              </span>
            )}
          </div>

          <div style={{ maxHeight: 320, overflowY: "auto", background: "#fffbeb" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#fef3c7", borderBottom: "1px solid #fde68a" }}>
                  <th style={{ padding: "5px 8px", fontSize: 10, fontWeight: 600, color: "#78350f", textAlign: "left", letterSpacing: "0.07em" }}>LOTTO</th>
                  <th style={{ padding: "5px 8px", fontSize: 10, fontWeight: 600, color: "#78350f", textAlign: "left", letterSpacing: "0.07em" }}>INDIRIZZO</th>
                  <th style={{ padding: "5px 8px", fontSize: 10, fontWeight: 600, color: "#78350f", textAlign: "center", letterSpacing: "0.07em" }}>LOCALI</th>
                  <th style={{ padding: "5px 8px", fontSize: 10, fontWeight: 600, color: "#78350f", textAlign: "center", letterSpacing: "0.07em" }}>MQ</th>
                  <th style={{ padding: "5px 8px", fontSize: 10, fontWeight: 600, color: "#78350f", textAlign: "center", letterSpacing: "0.07em" }}>APE</th>
                  <th style={{ padding: "5px 8px", fontSize: 10, fontWeight: 600, color: "#78350f", textAlign: "right", letterSpacing: "0.07em" }}>PREZZO BASE</th>
                  <th style={{ padding: "5px 8px", fontSize: 10, fontWeight: 600, color: "#78350f", textAlign: "center", letterSpacing: "0.07em" }}>DOC</th>
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
