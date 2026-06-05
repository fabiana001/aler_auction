import { MapContainer, TileLayer, Marker, Circle, useMap, useMapEvents } from "react-leaflet";
import { Icon, latLngBounds, latLng } from "leaflet";
import { useEffect } from "react";
import AuctionPopup from "./AuctionPopup";
import "leaflet/dist/leaflet.css";

const SHADOW = "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png";
const CM = "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img";

// Aggiudicata (~80%) — blue, high contrast on OSM beige/grey
const aggiudicataIcon = new Icon({
  iconUrl: `${CM}/marker-icon-blue.png`,
  iconRetinaUrl: `${CM}/marker-icon-2x-blue.png`,
  shadowUrl: SHADOW,
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

// Deserta — red-orange, signals failure
const desertaIcon = new Icon({
  iconUrl: `${CM}/marker-icon-red.png`,
  iconRetinaUrl: `${CM}/marker-icon-2x-red.png`,
  shadowUrl: SHADOW,
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

// Sconosciuto — grey, neutral/no data
const sconosciutoIcon = new Icon({
  iconUrl: `${CM}/marker-icon-grey.png`,
  iconRetinaUrl: `${CM}/marker-icon-2x-grey.png`,
  shadowUrl: SHADOW,
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

// Attiva — gold/amber, max contrast on OSM park green
const activeIcon = new Icon({
  iconUrl: `${CM}/marker-icon-gold.png`,
  iconRetinaUrl: `${CM}/marker-icon-2x-gold.png`,
  shadowUrl: SHADOW,
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

// Trend highlight — yellow, enlarged
const highlightIcon = new Icon({
  iconUrl: `${CM}/marker-icon-yellow.png`,
  iconRetinaUrl: `${CM}/marker-icon-2x-yellow.png`,
  shadowUrl: SHADOW,
  iconSize: [32, 52], iconAnchor: [16, 52], popupAnchor: [1, -44], shadowSize: [41, 41],
});

function outcomeIcon(auction) {
  const r = (auction.properties?.auction_result || "").toUpperCase();
  if (r === "AGGIUDICATA") return aggiudicataIcon;
  if (r.includes("DESERT")) return desertaIcon;
  return sconosciutoIcon;
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
        const icon = isHighlighted ? highlightIcon : outcomeIcon(auction);
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
