import { MapContainer, TileLayer, Marker, Circle, useMap, useMapEvents } from "react-leaflet";
import { Icon, latLngBounds, latLng } from "leaflet";
import { useEffect } from "react";
import AuctionPopup from "./AuctionPopup";
import "leaflet/dist/leaflet.css";

const defaultIcon = new Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Orange pin for recent auctions (last 12 months)
const recentIcon = new Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png",
  iconRetinaUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Green pin for active (upcoming) auction lots
const activeIcon = new Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
  iconRetinaUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Yellow/gold pin for trend-highlighted auctions
const highlightIcon = new Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png",
  iconRetinaUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [32, 52],
  iconAnchor: [16, 52],
  popupAnchor: [1, -44],
  shadowSize: [41, 41],
});

const MILAN_CENTER = [45.4642, 9.19];
const DEFAULT_ZOOM = 12;

const RECENT_CUTOFF_MS = Date.now() - 365 * 24 * 60 * 60 * 1000;
const IT_MONTHS = {
  gennaio:1, febbraio:2, marzo:3, aprile:4, maggio:5, giugno:6,
  luglio:7, agosto:8, settembre:9, ottobre:10, novembre:11, dicembre:12,
};

function parseItDate(s) {
  if (!s) return null;
  const m = s.trim().toLowerCase().match(/^(\d+)\s+(\w+)\s+(\d{4})$/);
  if (!m) return null;
  const mon = IT_MONTHS[m[2]];
  if (!mon) return null;
  return new Date(parseInt(m[3]), mon - 1, parseInt(m[1]));
}

function isRecent(auction) {
  const d = parseItDate(auction.properties?.auction_date);
  return d != null && d.getTime() >= RECENT_CUTOFF_MS;
}

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
    // Approximate degree offset for the given radius in meters
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

export default function AuctionMap({ auctions, center, circleCenter, radius, highlightedAuctions, onMarkerClick, onMapClick, selectedAuctionId, trendHighlightIds, activeLots }) {
  const displayAuctions = highlightedAuctions || auctions;
  const showFitBounds = !center && !highlightedAuctions && !circleCenter;
  const highlightSet = new Set(trendHighlightIds || []);
  const effectiveCircleCenter = circleCenter || center;

  return (
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
        const isSelected = auction.id === selectedAuctionId;
        const icon = isHighlighted ? highlightIcon : isRecent(auction) ? recentIcon : defaultIcon;
        return (
          <Marker
            key={auction.id}
            position={[auction.lat, auction.lng]}
            icon={icon}
            zIndexOffset={isHighlighted ? 1000 : isSelected ? 500 : 0}
            eventHandlers={{
              click: (e) => {
                // stopPropagation so the map click handler doesn't also fire
                e.originalEvent.stopPropagation();
                if (isSelected) {
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
            icon={activeIcon}
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
  );
}
