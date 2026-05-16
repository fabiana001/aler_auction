import { MapContainer, TileLayer, Marker, useMap } from "react-leaflet";
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

export default function AuctionMap({ auctions }) {
  return (
    <MapContainer
      center={MILAN_CENTER}
      zoom={DEFAULT_ZOOM}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds auctions={auctions} />
      {auctions.map((auction) => (
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
