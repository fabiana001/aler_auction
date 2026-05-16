import AuctionMap from "./components/MapContainer";
import { useAuctions } from "./hooks/useAuctions";

function App() {
  const { auctions, total, loading, error } = useAuctions();

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
        }}
      >
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>
          🗺️ Aste Immobiliari ALER — Milano
        </h1>
        {!loading && (
          <span style={{ fontSize: 13, opacity: 0.8 }}>
            {total} aste visualizzate
          </span>
        )}
      </header>

      <main style={{ flex: 1, position: "relative" }}>
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
        <AuctionMap auctions={auctions} />
      </main>
    </div>
  );
}

export default App;
