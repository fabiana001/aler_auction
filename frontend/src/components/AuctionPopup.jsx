import { Popup } from "react-leaflet";

function formatPrice(value) {
  if (value == null) return "N/A";
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function AuctionPopup({ auction }) {
  const p = auction.properties;

  return (
    <Popup>
      <div style={{ minWidth: 200, fontFamily: "system-ui, sans-serif" }}>
        <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 700 }}>
          {p.address || "Indirizzo sconosciuto"}
        </h3>
        <table style={{ fontSize: 12, borderCollapse: "collapse" }}>
          <tbody>
            <tr>
              <td style={{ padding: "2px 8px 2px 0", color: "#666" }}>Tipologia:</td>
              <td style={{ fontWeight: 600 }}>{p.property_type || "N/A"}</td>
            </tr>
            <tr>
              <td style={{ padding: "2px 8px 2px 0", color: "#666" }}>Prezzo base:</td>
              <td style={{ fontWeight: 600 }}>{formatPrice(p.base_price_eur)}</td>
            </tr>
            {p.final_offer_eur != null && (
              <tr>
                <td style={{ padding: "2px 8px 2px 0", color: "#666" }}>Offerta finale:</td>
                <td style={{ fontWeight: 600 }}>{formatPrice(p.final_offer_eur)}</td>
              </tr>
            )}
            {p.rooms != null && (
              <tr>
                <td style={{ padding: "2px 8px 2px 0", color: "#666" }}>Vani:</td>
                <td>{p.rooms}</td>
              </tr>
            )}
            {p.surface_sqm != null && (
              <tr>
                <td style={{ padding: "2px 8px 2px 0", color: "#666" }}>Superficie:</td>
                <td>{p.surface_sqm} m²</td>
              </tr>
            )}
            {p.base_price_per_sqm != null && (
              <tr>
                <td style={{ padding: "2px 8px 2px 0", color: "#666" }}>€/m²:</td>
                <td>{formatPrice(p.base_price_per_sqm)}</td>
              </tr>
            )}
            {p.auction_result && (
              <tr>
                <td style={{ padding: "2px 8px 2px 0", color: "#666" }}>Esito:</td>
                <td>{p.auction_result}</td>
              </tr>
            )}
            {p.auction_date && (
              <tr>
                <td style={{ padding: "2px 8px 2px 0", color: "#666" }}>Data asta:</td>
                <td>{p.auction_date}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Popup>
  );
}
