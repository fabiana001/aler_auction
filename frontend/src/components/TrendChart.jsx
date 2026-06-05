import { useState, useRef, useCallback } from "react";

function formatEur(v) {
  if (v == null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(v);
}

function formatAxisDate(iso) {
  const [y, m] = iso.split("-");
  return `${m}/${y.slice(2)}`;
}

export default function TrendChart({ timeSeries, avgPsm, onPointHover, hoveredDate, width = 330, height = 90, compact = false }) {
  const [tooltip, setTooltip] = useState(null);
  const svgRef = useRef(null);

  if (!timeSeries || timeSeries.length === 0) return null;

  const PAD = compact
    ? { top: 6, right: 8, bottom: 18, left: 44 }
    : { top: 12, right: 12, bottom: 28, left: 48 };
  const W = width - PAD.left - PAD.right;
  const H = height - PAD.top - PAD.bottom;

  const values = timeSeries.map((p) => p.avg_price_per_sqm).filter((v) => v != null);
  if (values.length === 0) return null;
  const minVal = Math.min(...values) * 0.9;
  const maxVal = Math.max(...values) * 1.1;

  // Date-based x scale so null-psm points don't shift the visible dots
  const dates = timeSeries.map((p) => new Date(p.date).getTime());
  const minDate = Math.min(...dates);
  const maxDate = Math.max(...dates);
  const dateSpan = maxDate - minDate || 1;
  const xScale = (i) => ((dates[i] - minDate) / dateSpan) * W;
  const yScale = (v) => H - ((v - minVal) / (maxVal - minVal)) * H;

  const validPoints = timeSeries.filter((p) => p.avg_price_per_sqm != null);
  const polylinePoints = validPoints
    .map((p) => `${xScale(timeSeries.indexOf(p))},${yScale(p.avg_price_per_sqm)}`)
    .join(" ");

  // Area: close at bottom
  const firstIdx = timeSeries.indexOf(validPoints[0]);
  const lastIdx = timeSeries.indexOf(validPoints[validPoints.length - 1]);
  const areaPath = [
    `M${xScale(firstIdx)},${H}`,
    ...validPoints.map((p) => `L${xScale(timeSeries.indexOf(p))},${yScale(p.avg_price_per_sqm)}`),
    `L${xScale(lastIdx)},${H}`,
    "Z",
  ].join(" ");

  const xLabelCount = Math.min(4, timeSeries.length);
  const xLabelIndices = timeSeries.length === 1
    ? [0]
    : Array.from({ length: xLabelCount }, (_, i) =>
        Math.round((i / (xLabelCount - 1)) * (timeSeries.length - 1))
      );

  const handleMouseMove = useCallback((e) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const mouseX = e.clientX - rect.left - PAD.left;

    let nearest = null;
    let minDist = Infinity;
    timeSeries.forEach((p, i) => {
      if (p.avg_price_per_sqm == null) return;
      const dist = Math.abs(xScale(i) - mouseX);
      if (dist < minDist) { minDist = dist; nearest = { i, p }; }
    });

    if (nearest && minDist < 30) {
      setTooltip({ x: xScale(nearest.i), y: yScale(nearest.p.avg_price_per_sqm), point: nearest.p });
      onPointHover && onPointHover(nearest.p.date, nearest.p.auction_ids || [], nearest.p);
    } else {
      setTooltip(null);
      onPointHover && onPointHover(null, [], null);
    }
  }, [timeSeries, onPointHover, PAD.left]);

  const handleMouseLeave = useCallback(() => {
    setTooltip(null);
    onPointHover && onPointHover(null, []);
  }, [onPointHover]);

  const ACCENT = "#2563EB";
  const GRID = "#e2e8f0";
  const TEXT_MUTED = "#64748b";

  return (
    <div style={{ position: "relative", userSelect: "none" }}>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ display: "block", overflow: "visible", cursor: "crosshair" }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={ACCENT} stopOpacity="0.12" />
            <stop offset="100%" stopColor={ACCENT} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <g transform={`translate(${PAD.left},${PAD.top})`}>
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((t) => (
            <line key={t} x1={0} y1={H * t} x2={W} y2={H * t} stroke={GRID} strokeWidth={t === 0 || t === 1 ? 1 : 0.5} />
          ))}
          {/* Y axis */}
          <line x1={0} y1={0} x2={0} y2={H} stroke={GRID} strokeWidth={1} />

          {/* Average reference line */}
          {avgPsm != null && avgPsm >= minVal && avgPsm <= maxVal && (
            <line x1={0} y1={yScale(avgPsm)} x2={W} y2={yScale(avgPsm)}
              stroke="var(--color-border-secondary)" strokeWidth={1} strokeDasharray="4 3" />
          )}

          {/* Area fill */}
          <path d={areaPath} fill="url(#areaGrad)" />

          {/* Line */}
          <polyline points={polylinePoints} fill="none" stroke={ACCENT}
            strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />

          {/* All data points */}
          {timeSeries.map((p, i) => {
            if (p.avg_price_per_sqm == null) return null;
            const isHovered = hoveredDate === p.date;
            return (
              <circle key={i}
                cx={xScale(i)} cy={yScale(p.avg_price_per_sqm)}
                r={isHovered ? 5 : 3}
                fill={isHovered ? "#fff" : ACCENT}
                stroke={isHovered ? ACCENT : "#fff"}
                strokeWidth={isHovered ? 2 : 1.5}
                style={{ pointerEvents: "none" }}
              />
            );
          })}

          {/* Vertical highlight line */}
          {tooltip && (
            <line x1={tooltip.x} y1={0} x2={tooltip.x} y2={H}
              stroke={ACCENT} strokeWidth={1} strokeDasharray="3 3" strokeOpacity={0.4}
              style={{ pointerEvents: "none" }}
            />
          )}

          {/* X-axis labels */}
          {xLabelIndices.map((idx) => (
            <text key={idx} x={xScale(idx)} y={H + 14}
              textAnchor="middle" fill={TEXT_MUTED} fontSize={9}
              fontFamily="var(--font-sans)">
              {formatAxisDate(timeSeries[idx].date)}
            </text>
          ))}

          {/* Y-axis labels */}
          {[0, 0.5, 1].map((t) => {
            const v = minVal + t * (maxVal - minVal);
            return (
              <text key={t} x={-6} y={yScale(v)} textAnchor="end"
                dominantBaseline="middle" fill={TEXT_MUTED} fontSize={9}
                fontFamily="var(--font-sans)">
                {v >= 1000 ? `${(v / 1000).toFixed(1)}k` : Math.round(v)}
              </text>
            );
          })}
        </g>
      </svg>

      {/* Tooltip */}
      {tooltip && (() => {
        const onRight = tooltip.x > W / 2;
        return (
          <div style={{
            position: "absolute",
            ...(onRight
              ? { right: width - PAD.left - tooltip.x + 12 }
              : { left: PAD.left + tooltip.x + 12 }),
            top: Math.max(4, PAD.top + tooltip.y - 10),
            background: "#ffffff",
            border: "1px solid #e2e8f0",
            borderRadius: 6,
            padding: "7px 11px",
            fontSize: 12,
            color: "#0f172a",
            pointerEvents: "none",
            whiteSpace: "nowrap",
            zIndex: 10,
            boxShadow: "0 4px 16px rgba(0,0,0,0.14)",
          }}>
            <div style={{ fontWeight: 600, color: "#2563EB", marginBottom: 3, fontSize: 11 }}>{tooltip.point.date}</div>
            <div style={{ fontWeight: 500 }}>€/m²: {formatEur(tooltip.point.avg_price_per_sqm)}</div>
            <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>
              {tooltip.point.count} {tooltip.point.count === 1 ? "asta" : "aste"}
            </div>
          </div>
        );
      })()}
    </div>
  );
}
