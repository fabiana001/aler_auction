import { useState, useEffect, useMemo } from "react";
import TrendChart from "./TrendChart";
import { fetchTrend } from "../utils/api";

const RADIUS_MIN = 250;
const RADIUS_MAX = 5000;
const RADIUS_DEFAULT = 1000;

function formatEur(v) {
  if (v == null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(v);
}

function outcomeInfo(result) {
  if (!result) return { bg: "#fafafa", color: "#52525b", border: "#d4d4d8", label: "Esito non disp.", activeBg: "#71717a" };
  const r = result.toUpperCase();
  if (r === "AGGIUDICATA") return { bg: "#eff6ff", color: "#1d4ed8", border: "#bfdbfe", label: "Aggiudicata", activeBg: "#2563eb" };
  if (r.includes("DESERT")) return { bg: "#fff7ed", color: "#9a3412", border: "#fed7aa", label: "Asta deserta", activeBg: "#c2410c" };
  return { bg: "#fafafa", color: "#52525b", border: "#d4d4d8", label: result, activeBg: "#71717a" };
}

function extractYear(dateStr) {
  if (!dateStr) return null;
  const m = dateStr.trim().match(/(\d{4})$/);
  return m ? parseInt(m[1]) : null;
}

function YearRangeSlider({ years, minYear, maxYear, onChange }) {
  const min = years[0];
  const max = years[years.length - 1];

  // Snap a raw integer value to the nearest available year
  function snap(v) {
    return years.reduce((best, y) => Math.abs(y - v) < Math.abs(best - v) ? y : best, years[0]);
  }

  const pctMin = ((minYear - min) / (max - min || 1)) * 100;
  const pctMax = ((maxYear - min) / (max - min || 1)) * 100;

  const ACCENT = "#1d4ed8";

  const thumbStyle = {
    WebkitAppearance: "none",
    appearance: "none",
    width: 14, height: 14,
    borderRadius: "50%",
    background: "#fff",
    border: `2px solid ${ACCENT}`,
    cursor: "pointer",
    boxShadow: "0 1px 4px rgba(0,0,0,0.18)",
    pointerEvents: "auto",
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1 }}>
      <span style={{ fontSize: 11, fontWeight: 500, color: ACCENT, minWidth: 30, textAlign: "right" }}>{minYear}</span>
      <div style={{ flex: 1, position: "relative", height: 20 }}>
        <style>{`
          .yr-slider { position:absolute; inset:0; width:100%; margin:0;
            WebkitAppearance:none; appearance:none; background:transparent;
            pointer-events:none; outline:none; }
          .yr-slider::-webkit-slider-thumb { -webkit-appearance:none; appearance:none;
            width:14px; height:14px; border-radius:50%; background:#fff;
            border:2px solid #1d4ed8; cursor:grab; pointer-events:auto;
            box-shadow:0 1px 4px rgba(0,0,0,0.18); }
          .yr-slider::-moz-range-thumb { width:14px; height:14px; border-radius:50%;
            background:#fff; border:2px solid #1d4ed8; cursor:grab;
            pointer-events:auto; box-shadow:0 1px 4px rgba(0,0,0,0.18); }
          .yr-slider::-webkit-slider-runnable-track { background:transparent; }
          .yr-slider::-moz-range-track { background:transparent; }
        `}</style>

        {/* Static track background */}
        <div style={{
          position: "absolute", top: "50%", left: 0, right: 0,
          height: 4, transform: "translateY(-50%)",
          background: "#e2e8f0", borderRadius: 2, pointerEvents: "none",
        }} />
        {/* Active range highlight */}
        <div style={{
          position: "absolute", top: "50%", transform: "translateY(-50%)",
          left: `${pctMin}%`, width: `${pctMax - pctMin}%`,
          height: 4, background: ACCENT, borderRadius: 2, pointerEvents: "none",
        }} />

        {/* Min range input */}
        <input
          type="range" className="yr-slider"
          min={min} max={max} step={1}
          value={minYear}
          onChange={(e) => {
            const v = snap(parseInt(e.target.value));
            onChange(Math.min(v, maxYear), maxYear);
          }}
          style={{ zIndex: minYear > max - (max - min) / 2 ? 5 : 3 }}
        />
        {/* Max range input */}
        <input
          type="range" className="yr-slider"
          min={min} max={max} step={1}
          value={maxYear}
          onChange={(e) => {
            const v = snap(parseInt(e.target.value));
            onChange(minYear, Math.max(v, minYear));
          }}
          style={{ zIndex: 4 }}
        />
      </div>
      <span style={{ fontSize: 11, fontWeight: 500, color: ACCENT, minWidth: 30 }}>{maxYear}</span>
    </div>
  );
}

function FilterChip({ label, active, onClick, activeBg = "#1d4ed8" }) {
  return (
    <button
      onClick={onClick}
      style={{
        fontSize: 11,
        fontWeight: 500,
        padding: "3px 10px",
        borderRadius: 3,
        border: "1px solid " + (active ? activeBg : "#e5e7eb"),
        background: active ? activeBg : "#f9fafb",
        color: active ? "#fff" : "#4b5563",
        cursor: "pointer",
        transition: "all 0.12s",
        whiteSpace: "nowrap",
        flexShrink: 0,
        letterSpacing: "0.04em",
      }}
      onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = "#e5e7eb"; }}
      onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = "#f9fafb"; }}
    >
      {label}
    </button>
  );
}

const API_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

function waybackUrl(sourceFile, sourceUrl) {
  if (!sourceFile || !sourceUrl) return null;
  const timestamp = sourceFile.replace(".html", "");
  return `https://web.archive.org/web/${timestamp}/${sourceUrl}`;
}


function pdfUrl(sourcePdf) {
  if (!sourcePdf) return null;
  return `${API_URL}/api/auctions/pdf/${encodeURIComponent(sourcePdf)}`;
}

function AuctionRow({ a }) {
  const p = a.properties || {};
  const info = outcomeInfo(p.auction_result);

  return (
    <div style={{
      padding: "9px 10px 9px 12px",
      borderRadius: "var(--border-radius-md)",
      cursor: "pointer",
      transition: "filter 0.1s",
      background: info.bg,
      border: "0.5px solid " + info.border,
      borderLeft: "3px solid " + info.activeBg,
      marginBottom: 4,
    }}
      onMouseEnter={(e) => { e.currentTarget.style.filter = "brightness(0.97)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.filter = "none"; }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 6, marginBottom: 4 }}>
        <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)", lineHeight: 1.3, flex: 1 }}>
          {p.address || "Indirizzo sconosciuto"}
        </span>
        <span style={{
          fontSize: 10, padding: "2px 7px", borderRadius: 3, fontWeight: 600, whiteSpace: "nowrap",
          background: info.activeBg, color: "#fff", letterSpacing: "0.03em",
        }}>
          {info.label}
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
        {p.auction_date && (
          <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 11, color: info.color }}>
            <i className="ti ti-calendar" style={{ fontSize: 11 }} />{p.auction_date}
          </span>
        )}
        {p.surface_sqm != null && (
          <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 11, color: "var(--color-text-secondary)", fontWeight: 500 }}>
            <i className="ti ti-ruler-2" style={{ fontSize: 11 }} />{p.surface_sqm} m²
          </span>
        )}
        {p.has_box && (
          <span style={{
            fontSize: 10, fontWeight: 600, padding: "1px 6px", borderRadius: 4,
            background: "#eff6ff", color: "#1d4ed8", border: "1px solid #bfdbfe",
          }}>
            + box
          </span>
        )}
        {p.property_type && !p.has_box && (
          <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>
            {p.property_type.toLowerCase()}
          </span>
        )}
      </div>
      {(p.base_price_eur != null || p.final_offer_eur != null) && (
        <div style={{ marginTop: 5, display: "flex", alignItems: "center", gap: 8 }}>
          {p.base_price_eur != null && (
            <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)", fontFamily: "var(--font-mono)" }}>
              Base: {formatEur(p.base_price_eur)}
            </span>
          )}
          {p.base_price_per_sqm != null && (
            <>
              <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>·</span>
              <span style={{ fontSize: 11, color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>{Math.round(p.base_price_per_sqm).toLocaleString("it-IT")} €/m²</span>
            </>
          )}
          {p.final_offer_eur != null && p.final_offer_eur > 0 && (
            <>
              <span style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>·</span>
              <span style={{ fontSize: 11, color: info.color, fontWeight: 500, fontFamily: "var(--font-mono)" }}>Agg.: {formatEur(p.final_offer_eur)}</span>
            </>
          )}
        </div>
      )}
      {((p.source_file && p.source_url) || p.source_pdf) && (
        <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 8 }}>
          {p.source_file && p.source_url && (
            <a
              href={waybackUrl(p.source_file, p.source_url)}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              style={{
                display: "inline-flex", alignItems: "center", gap: 3,
                fontSize: 10, color: "#2563EB", textDecoration: "none",
                padding: "2px 6px", borderRadius: 4,
                border: "0.5px solid #bfdbfe", background: "#eff6ff",
                fontWeight: 500,
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "#dbeafe"}
              onMouseLeave={(e) => e.currentTarget.style.background = "#eff6ff"}
            >
              <i className="ti ti-world" style={{ fontSize: 10 }} />
              Pagina asta
            </a>
          )}
          {p.source_pdf && (
            <a
              href={pdfUrl(p.source_pdf)}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              style={{
                display: "inline-flex", alignItems: "center", gap: 3,
                fontSize: 10, color: "#15803d", textDecoration: "none",
                padding: "2px 6px", borderRadius: 4,
                border: "0.5px solid #bbf7d0", background: "#f0fdf4",
                fontWeight: 500,
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "#dcfce7"}
              onMouseLeave={(e) => e.currentTarget.style.background = "#f0fdf4"}
            >
              <i className="ti ti-file-type-pdf" style={{ fontSize: 10 }} />
              Esito PDF
            </a>
          )}
        </div>
      )}
    </div>
  );
}

const OUTCOME_FILTERS = [
  { key: "tutte",       label: "Tutte",       activeBg: "#2563EB" },
  { key: "aggiudicate", label: "Aggiudicate", activeBg: "#2563eb" },
  { key: "deserte",     label: "Deserte",     activeBg: "#c2410c" },
];

function haversineMeters(lat1, lng1, lat2, lng2) {
  const R = 6371000;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export default function TrendPanel({ auction, onClose, onHoverIds, onRadiusChange, activeLots = [] }) {
  const [radius, setRadius] = useState(RADIUS_DEFAULT);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hoveredDate, setHoveredDate] = useState(null);
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [outcomeFilter, setOutcomeFilter] = useState("tutte");
  const [yearRange, setYearRange] = useState(null); // null = no filter, else [min, max]

  const handlePointHover = (date, ids, point) => {
    setHoveredDate(date);
    setHoveredPoint(point || null);
    onHoverIds && onHoverIds(ids || []);
  };

  const lat = auction?.lat;
  const lng = auction?.lng;
  const address = auction?.properties?.address || "Posizione selezionata";

  useEffect(() => {
    if (lat == null || lng == null) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setHoveredDate(null);
    setHoveredPoint(null);
    setYearRange(null);
    fetchTrend(lat, lng, radius)
      .then((d) => {
        if (!cancelled) {
          setData(d);
          setLoading(false);
          const allIds = (d.time_series || []).flatMap((p) => p.auction_ids || []);
          onRadiusChange && onRadiusChange({ lat, lng, radius, ids: allIds });
        }
      })
      .catch((e) => { if (!cancelled) { setError(e.message); setLoading(false); } });
    return () => { cancelled = true; };
  }, [lat, lng, radius]);

  if (!auction) return null;

  const timeSeries = data?.time_series || [];

  // All auctions across every time series point
  const allAuctions = useMemo(() => timeSeries.flatMap((p) => p.auctions || []), [timeSeries]);

  const availableYears = useMemo(() => {
    const years = new Set(allAuctions.map((a) => extractYear(a.properties?.auction_date)).filter(Boolean));
    return Array.from(years).sort();
  }, [allAuctions.length]);

  // Initialize year range to full extent when data loads
  useEffect(() => {
    if (availableYears.length >= 2) {
      setYearRange([availableYears[0], availableYears[availableYears.length - 1]]);
    } else {
      setYearRange(null);
    }
  }, [availableYears.join(',')]);

  const activeRange = useMemo(() =>
    yearRange ?? (availableYears.length >= 2
      ? [availableYears[0], availableYears[availableYears.length - 1]]
      : null),
  [yearRange, availableYears]);

  const isFullRange = !activeRange ||
    (activeRange[0] === availableYears[0] && activeRange[1] === availableYears[availableYears.length - 1]);

  // Filter the time series by year range — everything downstream uses this
  const filteredTimeSeries = useMemo(() => {
    if (isFullRange) return timeSeries;
    return timeSeries.filter((p) => {
      const y = p.date ? parseInt(p.date.slice(0, 4)) : null;
      return y != null && y >= activeRange[0] && y <= activeRange[1];
    });
  }, [timeSeries, activeRange, isFullRange]);

  // KPIs derived from filtered data
  const filteredCount = useMemo(() => {
    return filteredTimeSeries.reduce((acc, p) => acc + (p.auctions?.length ?? 0), 0);
  }, [filteredTimeSeries]);

  const filteredAvgPsm = useMemo(() => {
    const prices = filteredTimeSeries.flatMap((p) => p.auctions || [])
      .map((a) => a.properties?.base_price_per_sqm).filter((v) => v != null);
    return prices.length ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : null;
  }, [filteredTimeSeries]);

  const filteredAvgBase = useMemo(() => {
    const prices = filteredTimeSeries.flatMap((p) => p.auctions || [])
      .map((a) => a.properties?.base_price_eur).filter((v) => v != null);
    return prices.length ? prices.reduce((a, b) => a + b, 0) / prices.length : null;
  }, [filteredTimeSeries]);

  // Notify parent of the filtered IDs so map markers stay in sync
  useEffect(() => {
    const ids = filteredTimeSeries.flatMap((p) => p.auction_ids || []);
    onRadiusChange && onRadiusChange({ lat, lng, radius, ids });
  }, [filteredTimeSeries]);

  // Active lots within the current radius
  const nearbyActiveLots = useMemo(() => {
    if (!lat || !lng || !activeLots.length) return [];
    return activeLots.filter(
      (l) => l.lat != null && l.lng != null && haversineMeters(lat, lng, l.lat, l.lng) <= radius
    );
  }, [activeLots, lat, lng, radius]);

  // filteredTimeSeries is sorted ascending by ISO date; reverse gives newest-first
  const sourceList = hoveredPoint
    ? (hoveredPoint.auctions || [])
    : [...filteredTimeSeries].reverse().flatMap((p) => p.auctions || []);

  const filteredList = sourceList.filter((a) => {
    const result = (a.properties?.auction_result || "").toUpperCase();
    if (outcomeFilter === "aggiudicate" && result !== "AGGIUDICATA") return false;
    if (outcomeFilter === "deserte" && !result.includes("DESERT")) return false;
    return true;
  });

  const radiusLabel = radius >= 1000 ? `${(radius / 1000).toFixed(2)} km` : `${radius} m`;

  return (
    <div style={{
      width: 480,
      flexShrink: 0,
      background: "var(--color-background-primary)",
      borderLeft: "1px solid #e2e8f0",
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      animation: "slideInRight 0.22s ease-out",
      boxShadow: "var(--shadow-panel)",
    }}>
      <style>{`@keyframes slideInRight { from { transform: translateX(100%); } to { transform: translateX(0); } }`}</style>

      {/* Header */}
      <div style={{ padding: "14px 16px 12px", borderBottom: "0.5px solid #e2e8f0", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
          <i className="ti ti-map-pin" style={{ fontSize: 14, color: "var(--color-text-secondary)" }} />
          <span style={{
            fontSize: 11, fontWeight: 500, color: "var(--color-text-secondary)",
            textTransform: "uppercase", letterSpacing: "0.04em", flex: 1,
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
          }}>
            {address} — trend quartiere
          </span>
          <button onClick={onClose} style={{
            background: "none", border: "none", cursor: "pointer",
            color: "var(--color-text-tertiary)", fontSize: 16, padding: 0, lineHeight: 1,
            display: "flex", alignItems: "center", flexShrink: 0,
          }}>
            <i className="ti ti-x" />
          </button>
        </div>

        {/* Radius slider */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 12, color: "var(--color-text-tertiary)", minWidth: 50 }}>Raggio</span>
            <input
              type="range"
              min={RADIUS_MIN}
              max={RADIUS_MAX}
              step={250}
              value={radius}
              onChange={(e) => { setRadius(Number(e.target.value)); setHoveredDate(null); setHoveredPoint(null); onHoverIds && onHoverIds([]); }}
              style={{ flex: 1, accentColor: "var(--color-accent)" }}
            />
            <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)", minWidth: 52, textAlign: "right" }}>
              {radiusLabel}
            </span>
          </div>
        </div>

        {/* KPIs */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
          {[
            { val: filteredCount, unit: "aste nel raggio" },
            { val: filteredAvgPsm != null ? `${filteredAvgPsm.toLocaleString("it-IT")} €` : "—", unit: "€/m² medio" },
            { val: filteredAvgBase != null ? formatEur(filteredAvgBase) : "—", unit: "prezzo base medio" },
          ].map(({ val, unit }) => (
            <div key={unit} style={{
              background: "var(--color-background-secondary)",
              border: "1px solid var(--color-border-tertiary)",
              borderRadius: "var(--border-radius-md)",
              padding: "8px 10px",
            }}>
              <div style={{ fontSize: 16, fontWeight: 500, color: "var(--color-text-primary)", lineHeight: 1.1, fontFamily: "var(--font-mono)", letterSpacing: "-0.02em" }}>{val}</div>
              <div style={{ fontSize: 9, color: "var(--color-text-tertiary)", marginTop: 3, textTransform: "uppercase", letterSpacing: "0.05em" }}>{unit}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div style={{ padding: "10px 14px 8px", borderBottom: "0.5px solid #e2e8f0", flexShrink: 0 }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-tertiary)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 8 }}>
          €/m² nel tempo
        </div>
        {loading && (
          <div style={{ textAlign: "center", fontSize: 13, color: "var(--color-text-tertiary)", padding: "12px 0" }}>
            <i className="ti ti-loader-2" style={{ marginRight: 6 }} />Caricamento...
          </div>
        )}
        {error && (
          <div style={{ color: "var(--color-text-danger)", fontSize: 13, padding: "12px 0", textAlign: "center" }}>
            Errore: {error}
          </div>
        )}
        {!loading && !error && timeSeries.length === 0 && (
          <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", padding: "12px 0", textAlign: "center" }}>
            Nessun dato — prova ad aumentare il raggio.
          </div>
        )}
        {!loading && !error && filteredTimeSeries.length > 0 && (
          <TrendChart
            timeSeries={filteredTimeSeries}
            avgPsm={filteredAvgPsm}
            width={448}
            height={100}
            hoveredDate={hoveredDate}
            onPointHover={handlePointHover}
            compact
          />
        )}
        {!loading && !error && timeSeries.length > 0 && filteredTimeSeries.length === 0 && (
          <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", padding: "12px 0", textAlign: "center" }}>
            Nessun dato per il periodo selezionato.
          </div>
        )}
      </div>

      {/* Filters bar */}
      <div style={{
        padding: "8px 12px 8px",
        borderBottom: "0.5px solid #e2e8f0",
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}>
        {/* Row 1: count + outcome filters */}
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 11, fontWeight: 500, color: "var(--color-text-tertiary)", textTransform: "uppercase", letterSpacing: "0.06em", flex: 1, whiteSpace: "nowrap" }}>
            {hoveredPoint ? `${filteredList.length} aste del ${hoveredPoint.date}` : `${filteredList.length} aste`}
          </span>
          <div style={{ display: "flex", gap: 4 }}>
            {OUTCOME_FILTERS.map(({ key, label, activeBg }) => (
              <FilterChip
                key={key}
                label={label}
                active={outcomeFilter === key}
                activeBg={activeBg}
                onClick={() => setOutcomeFilter(key)}
              />
            ))}
          </div>
        </div>

        {/* Row 2: year range slider */}
        {availableYears.length >= 2 && activeRange && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 11, color: "var(--color-text-tertiary)", flexShrink: 0, display: "flex", alignItems: "center", gap: 3 }}>
              <i className="ti ti-calendar" style={{ fontSize: 11 }} />
            </span>
            <YearRangeSlider
              years={availableYears}
              minYear={activeRange[0]}
              maxYear={activeRange[1]}
              onChange={(min, max) => setYearRange([min, max])}
            />
            {!isFullRange && (
              <button
                onClick={() => setYearRange([availableYears[0], availableYears[availableYears.length - 1]])}
                title="Reset anni"
                style={{
                  background: "none", border: "none",
                  color: "#94a3b8", cursor: "pointer",
                  fontSize: 13, padding: 0, lineHeight: 1,
                  display: "flex", flexShrink: 0,
                }}
              >
                <i className="ti ti-x" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Auction list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "6px 8px 8px" }}>
        {/* Active auctions section */}
        {!hoveredPoint && nearbyActiveLots.length > 0 && (
          <div style={{ marginBottom: 8 }}>
            <div style={{
              fontSize: 10, fontWeight: 700, color: "#92400e", textTransform: "uppercase",
              letterSpacing: "0.06em", marginBottom: 4, paddingLeft: 2,
              display: "flex", alignItems: "center", gap: 4,
            }}>
              <i className="ti ti-gavel" style={{ fontSize: 10, color: "#92400e" }} /> Aste attive nel raggio ({nearbyActiveLots.length})
            </div>
            {nearbyActiveLots.map((lot) => (
              <div key={lot.lot_id} style={{
                padding: "9px 10px 9px 12px",
                borderRadius: "var(--border-radius-md)",
                background: "linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%)",
                border: "0.5px solid #fde68a",
                borderLeft: "3px solid #f59e0b",
                marginBottom: 4,
              }}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 6, marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)", lineHeight: 1.3, flex: 1 }}>
                    {lot.address}{lot.street_number ? ` ${lot.street_number}` : ""}
                    {lot.city && lot.city !== "MILANO" && (
                      <span style={{ fontSize: 11, color: "var(--color-text-secondary)", marginLeft: 4 }}>{lot.city}</span>
                    )}
                  </span>
                  <span style={{
                    fontSize: 10, padding: "2px 7px", borderRadius: 3, fontWeight: 600, whiteSpace: "nowrap",
                    background: "#f59e0b", color: "#fff", letterSpacing: "0.03em",
                  }}>
                    Attiva
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                  {lot.surface_sqm != null && (
                    <span style={{ display: "flex", alignItems: "center", gap: 3, fontSize: 11, color: "var(--color-text-secondary)", fontWeight: 500 }}>
                      <i className="ti ti-ruler-2" style={{ fontSize: 11 }} />{lot.surface_sqm} m²
                    </span>
                  )}
                  {lot.rooms != null && (
                    <span style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>{lot.rooms} loc.</span>
                  )}
                  {lot.has_box && (
                    <span style={{
                      fontSize: 10, fontWeight: 600, padding: "1px 6px", borderRadius: 4,
                      background: "#eff6ff", color: "#1d4ed8", border: "1px solid #bfdbfe",
                    }}>
                      + box
                    </span>
                  )}
                  {lot.ape_class && (
                    <span style={{ fontSize: 11, color: "#64748b", fontWeight: 600 }}>APE {lot.ape_class}</span>
                  )}
                </div>
                {lot.base_price_eur != null && (
                  <div style={{ marginTop: 5 }}>
                    <span style={{ fontSize: 12, fontWeight: 500, color: "var(--color-text-primary)", fontFamily: "var(--font-mono)" }}>
                      Base: {formatEur(lot.base_price_eur)}
                    </span>
                    {lot.surface_sqm && (
                      <>
                        <span style={{ fontSize: 11, color: "var(--color-text-tertiary)", margin: "0 6px" }}>·</span>
                        <span style={{ fontSize: 11, color: "var(--color-text-secondary)", fontFamily: "var(--font-mono)" }}>
                          {Math.round(lot.base_price_eur / lot.surface_sqm).toLocaleString("it-IT")} €/m²
                        </span>
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
            <div style={{ height: "0.5px", background: "#e2e8f0", margin: "8px 0" }} />
          </div>
        )}

        {filteredList.length === 0 && nearbyActiveLots.length === 0 && !loading && (
          <div style={{ padding: 20, textAlign: "center", fontSize: 13, color: "var(--color-text-tertiary)" }}>
            Nessuna asta trovata
          </div>
        )}
        {filteredList.length === 0 && nearbyActiveLots.length > 0 && !loading && (
          <div style={{ padding: "8px 0", textAlign: "center", fontSize: 12, color: "var(--color-text-tertiary)" }}>
            Nessuna asta storica trovata
          </div>
        )}
        {filteredList.map((a) => (
          <AuctionRow key={a.id} a={a} />
        ))}
      </div>
    </div>
  );
}
