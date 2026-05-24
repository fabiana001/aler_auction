import { MapContainer, TileLayer, Marker, Circle, useMap } from "react-leaflet";
import { Icon } from "leaflet";
import { useEffect } from "react";
import AuctionPopup from "./AuctionPopup";
import "leaflet/dist/leaflet.css";

// Fix default marker icon issue with bundlers
const defaultIcon = new Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

// Center: Milan
const MILAN_CENTER = [45.4642, 9.19];
const DEFAULT_ZOOM = 12;

function FitBounds({ auctions }) {
  const map = useMap();

  useEffect(() => {
    if (auctions.length === 0) return;
    const bounds = auctions.map((a) => [a.lat, a.lng]);
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
    }
  }, [auctions, map]);

  return null;
}

function FlyToCenter({ center }) {
  const map = useMap();

  useEffect(() => {
    if (center && center[0] != null && center[1] != null) {
      map.flyTo(center, 16, { duration: 0.8 });
    }
  }, [center, map]);

  return null;
}

export default function AuctionMap({ auctions, center, radius, highlightedAuctions }) {
  const displayAuctions = highlightedAuctions || auctions;
  const showFitBounds = !center && !highlightedAuctions;

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
      {showFitBounds && <FitBounds auctions={displayAuctions} />}
      {center && <FlyToCenter center={center} />}
      {center && radius && (
        <Circle
          center={center}
          radius={radius}
          pathOptions={{ color: "#4a4aaa", fillColor: "#4a4aaa", fillOpacity: 0.1, weight: 2, dashArray: "6 4" }}
        />
      )}
      {displayAuctions.map((auction) => (
        <Marker
          key={auction.id}
          position={[auction.lat, auction.lng]}
          icon={defaultIcon}
        >
          <AuctionPopup auction={auction} />
        </Marker>
      ))}
    </MapContainer>
  );
}
