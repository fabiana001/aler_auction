import AuctionMap from "../components/MapContainer";
import SearchBar from "../components/SearchBar";
import NearbyPanel from "../components/NearbyPanel";
import NewAuctionsBanner from "../components/NewAuctionsBanner";
import ActiveAuctionPanel from "../components/ActiveAuctionPanel";
import TrendPanel from "../components/TrendPanel";
import { useAuctions } from "../hooks/useAuctions";
import { fetchNearby, fetchActiveAuction } from "../utils/api";
import { useState, useCallback, useMemo, useEffect } from "react";

function App() {
  const { auctions, total, loading, error } = useAuctions();
  const [searchLocation, setSearchLocation] = useState(null);
  const [nearbyAuctions, setNearbyAuctions] = useState(null);
  const [nearbyRadius, setNearbyRadius] = useState(500);
  const [showNearby, setShowNearby] = useState(false);
  const [selectedAuction, setSelectedAuction] = useState(null);
  const [trendHighlightIds, setTrendHighlightIds] = useState([]);
  const [trendRadius, setTrendRadius] = useState(null);
  const [activeAuctionData, setActiveAuctionData] = useState(null);

  useEffect(() => {
    fetchActiveAuction().then(setActiveAuctionData).catch(() => {});
  }, []);

  const handleSearchSelect = useCallback(async ({ lat, lng }) => {
    if (lat == null || lng == null) return;
    setSearchLocation({ lat, lng });
    setNearbyRadius(500);
    if (!selectedAuction) {
      setShowNearby(true);
    }
    try {
      const data = await fetchNearby(lat, lng, 500);
      const items = Array.isArray(data) ? data : data.items || [];
      setNearbyAuctions(items);
    } catch {
      setNearbyAuctions([]);
    }
  }, [selectedAuction]);

  const handleCloseNearby = useCallback(() => {
    setShowNearby(false);
    setSearchLocation(null);
    setNearbyAuctions(null);
  }, []);

  const handleMarkerClick = useCallback((auction) => {
    setSelectedAuction(auction);
    setShowNearby(false);
    setTrendRadius(null);
    setTrendHighlightIds([]);
  }, []);

  const handleBannerPinClick = useCallback((auction) => {
    setSelectedAuction(auction);
    setShowNearby(false);
    setTrendRadius(null);
    setTrendHighlightIds([]);
  }, []);

  const handleCloseTrend = useCallback(() => {
    setSelectedAuction(null);
    setTrendHighlightIds([]);
    setTrendRadius(null);
  }, []);

  const handleTrendRadiusChange = useCallback((info) => {
    setTrendRadius(info);
    setTrendHighlightIds([]);
  }, []);

  // Click on empty map area or Escape → close any open panel
  const handleMapClick = useCallback(() => {
    if (showNearby) {
      setShowNearby(false);
      setSearchLocation(null);
      setNearbyAuctions(null);
    }
    if (selectedAuction) {
      setSelectedAuction(null);
      setTrendHighlightIds([]);
      setTrendRadius(null);
    }
  }, [showNearby, selectedAuction]);

  useEffect(() => {
    function onKeyDown(e) {
      if (e.key === "Escape") handleMapClick();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [handleMapClick]);

  const trendRadiusIdSet = useMemo(
    () => new Set(trendRadius?.ids || []),
    [trendRadius]
  );

  const displayAuctions = useMemo(() => {
    if (!selectedAuction || !trendRadius || searchLocation) return auctions;
    return auctions.filter((a) => trendRadiusIdSet.has(a.id));
  }, [auctions, selectedAuction, trendRadius, trendRadiusIdSet, searchLocation]);

  const mapCenter = searchLocation
    ? [searchLocation.lat, searchLocation.lng]
    : selectedAuction && trendRadius && selectedAuction.lat != null
    ? [selectedAuction.lat, selectedAuction.lng]
    : undefined;

  const mapRadius = selectedAuction && trendRadius && selectedAuction.lat != null
    ? trendRadius.radius
    : showNearby ? nearbyRadius : undefined;

  const mapCircleCenter = selectedAuction && trendRadius && selectedAuction.lat != null
    ? [selectedAuction.lat, selectedAuction.lng]
    : searchLocation
    ? [searchLocation.lat, searchLocation.lng]
    : undefined;

  const asteCount = selectedAuction && trendRadius
    ? displayAuctions.length
    : total;

  const showPanel = showNearby || !!selectedAuction;

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", background: "var(--color-background-secondary)" }}>
      {/* Top bar */}
      <header style={{
        height: 48,
        padding: "0 20px",
        background: "var(--color-background-primary)",
        borderBottom: "0.5px solid var(--color-border-secondary)",
        display: "flex",
        alignItems: "center",
        gap: 0,
        flexShrink: 0,
        position: "relative",
        zIndex: 1000,
      }}>
        <i className="ti ti-building" style={{ fontSize: 16, color: "#374151", flexShrink: 0 }} />
        <span style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)", whiteSpace: "nowrap", letterSpacing: "0.01em", marginLeft: 8 }}>
          Aste ALER <span style={{ fontWeight: 400, color: "var(--color-text-tertiary)" }}>Milano</span>
        </span>
        <div style={{ width: "0.5px", height: 18, background: "var(--color-border-secondary)", margin: "0 16px", flexShrink: 0 }} />
        <SearchBar onSelect={handleSearchSelect} />
        {!loading && !selectedAuction && (
          <span style={{
            fontSize: 11,
            color: "var(--color-text-secondary)",
            background: "var(--color-background-secondary)",
            border: "0.5px solid var(--color-border-tertiary)",
            borderRadius: 3,
            padding: "3px 10px",
            whiteSpace: "nowrap",
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.03em",
          }}>
            {asteCount} aste
          </span>
        )}
        {(showNearby || selectedAuction) && (
          <button
            onClick={handleMapClick}
            title="Chiudi pannello (Esc)"
            style={{
              marginLeft: "auto",
              display: "flex",
              alignItems: "center",
              gap: 5,
              fontSize: 11,
              color: "var(--color-text-secondary)",
              background: "var(--color-background-secondary)",
              border: "0.5px solid var(--color-border-secondary)",
              borderRadius: 3,
              padding: "3px 10px",
              cursor: "pointer",
              whiteSpace: "nowrap",
              transition: "background 0.1s",
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "#e2e8f0"}
            onMouseLeave={(e) => e.currentTarget.style.background = "var(--color-background-secondary)"}
          >
            <i className="ti ti-x" style={{ fontSize: 11 }} />
            Chiudi <kbd style={{ fontSize: 10, opacity: 0.6, marginLeft: 2 }}>Esc</kbd>
          </button>
        )}
      </header>

      {/* Main: map + side panel */}
      <main style={{ flex: 1, display: "flex", overflow: "hidden", position: "relative" }}>
        {/* Map area */}
        <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
          <div style={{ position: "absolute", top: 0, left: 0, right: 0, zIndex: 3100, display: "flex", flexDirection: "column" }}>
            <ActiveAuctionPanel data={activeAuctionData} onLotClick={handleBannerPinClick} />
            <NewAuctionsBanner onPinClick={handleBannerPinClick} />
          </div>

          {loading && (
            <div style={{
              position: "absolute", inset: 0,
              display: "flex", alignItems: "center", justifyContent: "center",
              background: "rgba(255,255,255,0.85)", zIndex: 1000, fontSize: 13,
              color: "var(--color-text-secondary)",
            }}>
              <i className="ti ti-loader" style={{ marginRight: 8 }} />
              Caricamento aste...
            </div>
          )}
          {error && (
            <div style={{
              position: "absolute", top: 16, left: "50%", transform: "translateX(-50%)",
              background: "var(--color-background-danger)", color: "var(--color-text-danger)",
              border: "0.5px solid #fca5a5",
              padding: "8px 16px", borderRadius: "var(--border-radius-md)",
              zIndex: 1000, fontSize: 13,
            }}>
              Errore: {error}
            </div>
          )}

          <AuctionMap
            auctions={displayAuctions}
            center={mapCenter}
            circleCenter={mapCircleCenter}
            radius={mapRadius}
            highlightedAuctions={showNearby ? nearbyAuctions : undefined}
            onMarkerClick={handleMarkerClick}
            onMapClick={handleMapClick}
            selectedAuctionId={selectedAuction?.id}
            activeLots={(activeAuctionData?.lots || []).filter(l => l.lat != null)}
            trendHighlightIds={trendHighlightIds}
          />
        </div>

        {/* Side panel */}
        {showNearby && (
          <NearbyPanel location={searchLocation} onClose={handleCloseNearby} />
        )}
        {selectedAuction && (
          <TrendPanel
            auction={selectedAuction}
            onClose={handleCloseTrend}
            onHoverIds={setTrendHighlightIds}
            onRadiusChange={handleTrendRadiusChange}
            activeLots={activeAuctionData?.lots || []}
          />
        )}
      </main>
    </div>
  );
}

export default App;
