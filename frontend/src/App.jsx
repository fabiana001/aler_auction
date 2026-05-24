import AuctionMap from "./components/MapContainer";
import SearchBar from "./components/SearchBar";
import NearbyPanel from "./components/NearbyPanel";
import { useAuctions } from "./hooks/useAuctions";
import { fetchNearby } from "./utils/api";
import { useState, useCallback } from "react";

function App() {
  const { auctions, total, loading, error } = useAuctions();
  const [searchLocation, setSearchLocation] = useState(null);
  const [nearbyAuctions, setNearbyAuctions] = useState(null);
  const [nearbyRadius, setNearbyRadius] = useState(500);
  const [showPanel, setShowPanel] = useState(false);

  const handleSearchSelect = useCallback(async ({ lat, lng }) => {
    if (lat == null || lng == null) return;
    setSearchLocation({ lat, lng });
    setNearbyRadius(500);
    setShowPanel(true);
    try {
      const data = await fetchNearby(lat, lng, 500);
      const items = Array.isArray(data) ? data : data.items || [];
      setNearbyAuctions(items);
    } catch {
      setNearbyAuctions([]);
    }
  }, []);

  const handleClosePanel = useCallback(() => {
    setShowPanel(false);
    setSearchLocation(null);
    setNearbyAuctions(null);
  }, []);

  const mapCenter = searchLocation ? [searchLocation.lat, searchLocation.lng] : undefined;

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          padding: "12px 20px",
          background: "#1a1a2e",
          color: "#fff",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexShrink: 0,
          gap: 16,
        }}
      >
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, whiteSpace: "nowrap" }}>
          🗺️ Aste Immobiliari ALER — Milano
        </h1>
        <SearchBar onSelect={handleSearchSelect} />
        {!loading && (
          <span style={{ fontSize: 13, opacity: 0.8, whiteSpace: "nowrap" }}>
            {total} aste visualizzate
          </span>
        )}
      </header>

      <main style={{ flex: 1, position: "relative" }}>
        {showPanel && (
          <NearbyPanel
            location={searchLocation}
            onClose={handleClosePanel}
          />
        )}
        {loading && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(255,255,255,0.8)",
              zIndex: 1000,
              fontSize: 16,
            }}
          >
            Caricamento aste...
          </div>
        )}
        {error && (
          <div
            style={{
              position: "absolute",
              top: 16,
              left: "50%",
              transform: "translateX(-50%)",
              background: "#fee",
              color: "#c00",
              padding: "8px 16px",
              borderRadius: 6,
              zIndex: 1000,
              fontSize: 14,
            }}
          >
            Errore: {error}
          </div>
        )}
        <AuctionMap
          auctions={auctions}
          center={mapCenter}
          radius={showPanel ? nearbyRadius : undefined}
          highlightedAuctions={showPanel ? nearbyAuctions : undefined}
        />
      </main>
    </div>
  );
}

export default App;
