import { MapContainer, TileLayer, Marker, Circle, useMap, useMapEvents } from "react-leaflet";
import { divIcon, latLngBounds, latLng } from "leaflet";
import { useEffect } from "react";
import AuctionPopup from "./AuctionPopup";
import "leaflet/dist/leaflet.css";

const PIN_COLORS = {
  aggiudicata: "#16A34A",
  deserta:     "#D97706",
  nd:          "#6B7280",
  live:        "#2563EB",
};

function makePinIcon(color, size = 28) {
  const half = size / 2;
  return divIcon({
    className: "",
    iconSize: [size, size],
    iconAnchor: [half, size],
    popupAnchor: [0, -size],
    html: `<div style="
      width:${size}px;height:${size}px;
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      background:${color};
      border:2px solid #fff;
      box-shadow:0 2px 6px rgba(0,0,0,0.18);
      display:flex;align-items:center;justify-content:center;
    "></div>`,
  });
}

function makeHighlightIcon() {
  return makePinIcon("#2563EB", 36);
}

const icons = {
  aggiudicata: makePinIcon(PIN_COLORS.aggiudicata),
  deserta:     makePinIcon(PIN_COLORS.deserta),
  nd:          makePinIcon(PIN_COLORS.nd),
  live:        makePinIcon(PIN_COLORS.live),
  highlight:   makeHighlightIcon(),
};

function outcomeIcon(auction) {
  const r = (auction.properties?.auction_result || "").toUpperCase();
  if (r === "AGGIUDICATA") return icons.aggiudicata;
  if (r.includes("DESERT")) return icons.deserta;
  return icons.nd;
}

const MILAN_CENTER = [45.4642, 9.19];
const DEFAULT_ZOOM = 12;

function FitBounds({ auctions }) {
  const map = useMap();
  useEffect(() => {
    if (auctions.length === 0) return;
    const bounds = auctions.map((a) => [a.lat, a.lng]);
    map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
  }, [auctions, map]);
  return null;
}

function FlyToCenter({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] != null) map.flyTo(center, 16, { duration: 0.8 });
  }, [center, map]);
  return null;
}

function MapClickHandler({ onMapClick }) {
  useMapEvents({ click: onMapClick });
  return null;
}

function FitCircle({ center, radius }) {
  const map = useMap();
  useEffect(() => {
    if (!center || !radius) return;
    const latOffset = (radius / 111320);
    const lngOffset = (radius / (111320 * Math.cos((center[0] * Math.PI) / 180)));
    const bounds = latLngBounds(
      latLng(center[0] - latOffset, center[1] - lngOffset),
      latLng(center[0] + latOffset, center[1] + lngOffset)
    );
    map.fitBounds(bounds, { padding: [40, 40] });
  }, [center, radius, map]);
  return null;
}

const LEGEND_ITEMS = [
  { color: PIN_COLORS.aggiudicata, label: "Aggiudicata" },
  { color: PIN_COLORS.deserta,     label: "Deserta" },
  { color: PIN_COLORS.nd,          label: "Esito N/D" },
];

function MapLegend() {
  return (
    <div style={{
      position: "absolute",
      bottom: 40,
      left: 12,
      background: "var(--color-background-primary)",
      border: "0.5px solid var(--color-border-secondary)",
      borderRadius: 8,
      padding: "8px 12px",
      display: "flex",
      flexDirection: "column",
      gap: 5,
      zIndex: 10,
      fontSize: 11,
      color: "var(--color-text-secondary)",
      fontFamily: "var(--font-sans)",
      pointerEvents: "none",
    }}>
      {LEGEND_ITEMS.map(({ color, label }) => (
        <div key={label} style={{ display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{
            width: 9, height: 9, borderRadius: "50%",
            background: color, display: "inline-block", flexShrink: 0,
          }} />
          {label}
        </div>
      ))}
    </div>
  );
}

export default function AuctionMap({ auctions, center, circleCenter, radius, highlightedAuctions, onMarkerClick, onMapClick, selectedAuctionId, trendHighlightIds, activeLots }) {
  const displayAuctions = highlightedAuctions || auctions;
  const showFitBounds = !center && !highlightedAuctions && !circleCenter;
  const highlightSet = new Set(trendHighlightIds || []);
  const effectiveCircleCenter = circleCenter || center;

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      <MapContainer
        center={center || MILAN_CENTER}
        zoom={center ? 16 : DEFAULT_ZOOM}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {onMapClick && <MapClickHandler onMapClick={onMapClick} />}
        {showFitBounds && <FitBounds auctions={displayAuctions} />}
        {effectiveCircleCenter && radius
          ? <FitCircle center={effectiveCircleCenter} radius={radius} />
          : center && <FlyToCenter center={center} />
        }
        {effectiveCircleCenter && radius && (
          <Circle
            center={effectiveCircleCenter}
            radius={radius}
            pathOptions={{ color: "#2563EB", fillColor: "#2563EB", fillOpacity: 0.04, weight: 1.5, dashArray: "6 4" }}
          />
        )}
        {displayAuctions.map((auction) => {
          const isHighlighted = highlightSet.has(auction.id);
          const icon = isHighlighted ? icons.highlight : outcomeIcon(auction);
          return (
            <Marker
              key={auction.id}
              position={[auction.lat, auction.lng]}
              icon={icon}
              zIndexOffset={isHighlighted ? 1000 : auction.id === selectedAuctionId ? 500 : 0}
              eventHandlers={{
                click: (e) => {
                  e.originalEvent.stopPropagation();
                  if (auction.id === selectedAuctionId) {
                    onMapClick && onMapClick();
                  } else {
                    onMarkerClick && onMarkerClick(auction);
                  }
                },
              }}
            >
              <AuctionPopup auction={auction} />
            </Marker>
          );
        })}
        {(activeLots || []).map((lot) => {
          const lotAuction = {
            lat: lot.lat,
            lng: lot.lng,
            properties: {
              address: `${lot.address} ${lot.street_number || ""}`.trim(),
              city: lot.city,
              surface_sqm: lot.surface_sqm,
              base_price_eur: lot.base_price_eur,
              property_type: lot.property_type,
              auction_date: lot.auction_date,
              auction_result: "ASTA ATTIVA",
            },
          };
          return (
            <Marker
              key={`active-${lot.lot_id}`}
              position={[lot.lat, lot.lng]}
              icon={icons.live}
              zIndexOffset={2000}
              eventHandlers={{
                click: (e) => {
                  e.originalEvent.stopPropagation();
                  onMarkerClick && onMarkerClick(lotAuction);
                },
              }}
            >
              <AuctionPopup auction={lotAuction} />
            </Marker>
          );
        })}
      </MapContainer>
      <MapLegend />
    </div>
  );
}
