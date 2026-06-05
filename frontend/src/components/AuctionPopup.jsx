import { Popup } from "react-leaflet";

function formatPrice(value) {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

function ResultBadge({ result }) {
  if (!result) return null;
  const r = result.toUpperCase();
  let bg, color, label;
  if (r === "AGGIUDICATA") {
    bg = "#f0fdf4"; color = "#15803d"; label = "Aggiudicata";
  } else if (r.includes("DESERT")) {
    bg = "#fffbeb"; color = "#92400e"; label = "Deserta";
  } else {
    bg = "#fef2f2"; color = "#b91c1c"; label = result;
  }
  return (
    <span style={{
      display: "inline-block", padding: "2px 7px", borderRadius: 20,
      fontSize: 10, fontWeight: 500, background: bg, color,
    }}>
      {label}
    </span>
  );
}

export default function AuctionPopup({ auction }) {
  const p = auction.properties;

  return (
    <Popup>
      <div style={{ minWidth: 200, fontFamily: "system-ui, sans-serif", fontSize: 13 }}>
        <div style={{ fontWeight: 500, color: "#0f172a", marginBottom: 6, lineHeight: 1.3 }}>
          {p.address || "Indirizzo sconosciuto"}
        </div>
        {p.auction_result && (
          <div style={{ marginBottom: 8 }}>
            <ResultBadge result={p.auction_result} />
          </div>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {[
            ["Tipologia", p.property_type],
            ["Prezzo base", p.base_price_eur != null ? formatPrice(p.base_price_eur) : null],
            ["Offerta finale", p.final_offer_eur != null && p.final_offer_eur > 0 ? formatPrice(p.final_offer_eur) : null],
            ["Superficie", p.surface_sqm != null ? `${p.surface_sqm} m²` : null],
            ["€/m²", p.base_price_per_sqm != null ? formatPrice(p.base_price_per_sqm) : null],
            ["Data asta", p.auction_date],
          ].filter(([, v]) => v != null).map(([label, value]) => (
            <div key={label} style={{ display: "flex", gap: 6, alignItems: "baseline" }}>
              <span style={{ color: "#94a3b8", fontSize: 11, minWidth: 76 }}>{label}:</span>
              <span style={{ fontWeight: 500, color: "#0f172a", fontSize: 12 }}>{value}</span>
            </div>
          ))}
        </div>
      </div>
    </Popup>
  );
}
