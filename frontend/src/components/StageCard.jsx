import { useState, useEffect, useRef, useCallback } from "react";
import { openLogStream } from "../utils/pipelineApi";

const COLORS = {
  bg: "#0f0f23",
  surface: "#1a1a2e",
  surfaceHover: "#16213e",
  border: "#2a2a4a",
  primary: "#4a4aaa",
  accent: "#6c63ff",
  success: "#22c55e",
  error: "#ef4444",
  warning: "#f59e0b",
  text: "#eee",
  textMuted: "#888",
};

const STATUS_LABELS = {
  idle: { label: "In attesa", color: "#888", icon: "○" },
  running: { label: "In esecuzione", color: "#6c63ff", icon: "◉" },
  done: { label: "Completato", color: "#22c55e", icon: "✓" },
  error: { label: "Errore", color: "#ef4444", icon: "✗" },
};

function formatDuration(startedAt, finishedAt) {
  if (!startedAt) return "—";
  const start = new Date(startedAt);
  const end = finishedAt ? new Date(finishedAt) : new Date();
  const diffMs = end - start;
  const totalSec = Math.floor(diffMs / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  if (min > 0) return `${min}m ${sec}s`;
  return `${sec}s`;
}

function parseSummary(summary) {
  if (!summary) return [];
  if (typeof summary === "string") {
    try {
      summary = JSON.parse(summary);
    } catch {
      return [{ label: summary }];
    }
  }
  if (typeof summary === "object") {
    return Object.entries(summary).map(([key, value]) => ({
      label: `${key}: ${value}`,
      key,
      value,
    }));
  }
  return [];
}

export default function StageCard({ step, onRun, onStop, onOpenLog }) {
  const [expanded, setExpanded] = useState(false);
  const [liveLogs, setLiveLogs] = useState([]);
  const [elapsed, setElapsed] = useState("");
  const logEndRef = useRef(null);
  const closeStreamRef = useRef(null);
  const timerRef = useRef(null);

  const status = step.status || "idle";
  const statusInfo = STATUS_LABELS[status] || STATUS_LABELS.idle;
  const isRunning = status === "running";
  const summaryItems = parseSummary(step.summary);

  // Live elapsed timer
  useEffect(() => {
    if (isRunning && step.started_at) {
      const update = () => {
        setElapsed(formatDuration(step.started_at, null));
      };
      update();
      timerRef.current = setInterval(update, 1000);
      return () => {
        if (timerRef.current) clearInterval(timerRef.current);
      };
    } else {
      setElapsed(formatDuration(step.started_at, step.finished_at));
      if (timerRef.current) clearInterval(timerRef.current);
    }
  }, [isRunning, step.started_at, step.finished_at]);

  // SSE log stream
  const startLogStream = useCallback(() => {
    if (closeStreamRef.current) return;
    setLiveLogs([]);
    const close = openLogStream(step.id, (line) => {
      setLiveLogs((prev) => {
        const next = [...prev, line];
        if (next.length > 200) next.shift();
        return next;
      });
    });
    closeStreamRef.current = close;
  }, [step.id]);

  const stopLogStream = useCallback(() => {
    if (closeStreamRef.current) {
      closeStreamRef.current();
      closeStreamRef.current = null;
    }
  }, []);

  // Auto-scroll logs
  useEffect(() => {
    if (expanded && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [liveLogs, expanded]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopLogStream();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [stopLogStream]);

  const handleToggleExpand = () => {
    const next = !expanded;
    setExpanded(next);
    if (next && isRunning) {
      startLogStream();
    } else if (!next) {
      stopLogStream();
    }
  };

  const handleAction = () => {
    if (isRunning) {
      onStop(step.id);
    } else {
      onRun(step.id);
    }
  };

  const displayLogs = isRunning ? liveLogs : (step.logs || []);

  return (
    <>
      <style>{`
        @keyframes pulseGlow {
          0%, 100% { box-shadow: 0 0 8px 0 rgba(108, 99, 255, 0.3); }
          50% { box-shadow: 0 0 20px 4px rgba(108, 99, 255, 0.6); }
        }
        @keyframes progressSlide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .stage-card {
          background: ${COLORS.surface};
          border: 1px solid ${COLORS.border};
          border-radius: 12px;
          padding: 16px;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
          animation: fadeIn 0.3s ease;
        }
        .stage-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        }
        .stage-card.running {
          animation: pulseGlow 2s ease-in-out infinite;
          border-color: ${COLORS.accent};
        }
        .stage-card.done {
          border-color: ${COLORS.success};
        }
        .stage-card.error {
          border-color: ${COLORS.error};
        }
        .progress-bar-container {
          height: 3px;
          background: ${COLORS.border};
          border-radius: 2px;
          overflow: hidden;
          margin: 8px 0;
        }
        .progress-bar-running {
          height: 100%;
          width: 50%;
          background: linear-gradient(90deg, transparent, ${COLORS.accent}, transparent);
          animation: progressSlide 1.5s ease-in-out infinite;
        }
        .log-panel {
          background: #0d1117;
          border-radius: 8px;
          padding: 10px 12px;
          margin-top: 10px;
          max-height: 200px;
          overflow-y: auto;
          font-family: ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace;
          font-size: 12px;
          line-height: 1.6;
          color: #c9d1d9;
          border: 1px solid ${COLORS.border};
        }
        .log-panel::-webkit-scrollbar {
          width: 6px;
        }
        .log-panel::-webkit-scrollbar-track {
          background: #0d1117;
        }
        .log-panel::-webkit-scrollbar-thumb {
          background: ${COLORS.border};
          border-radius: 3px;
        }
        .log-line {
          white-space: pre-wrap;
          word-break: break-all;
        }
        .log-line.error-line {
          color: ${COLORS.error};
        }
        .log-line.warn-line {
          color: ${COLORS.warning};
        }
      `}</style>

      <div className={`stage-card ${status}`}>
        {/* Header row */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <span style={{ fontSize: 24, lineHeight: 1 }}>{step.icon || "📦"}</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontWeight: 600, fontSize: 15, color: COLORS.text, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {step.name || step.id}
            </div>
          </div>
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: "3px 8px",
              borderRadius: 12,
              background: statusInfo.color + "22",
              color: statusInfo.color,
              border: `1px solid ${statusInfo.color}44`,
              whiteSpace: "nowrap",
            }}
          >
            {statusInfo.icon} {statusInfo.label}
          </span>
        </div>

        {/* Progress bar when running */}
        {isRunning && (
          <div className="progress-bar-container">
            <div className="progress-bar-running" />
          </div>
        )}

        {/* Duration */}
        <div style={{ fontSize: 12, color: COLORS.textMuted, marginBottom: 8 }}>
          ⏱ {elapsed}
        </div>

        {/* Summary */}
        {summaryItems.length > 0 && (
          <div style={{ marginBottom: 8 }}>
            {summaryItems.map((item, i) => (
              <div key={i} style={{ fontSize: 12, color: COLORS.success, padding: "2px 0" }}>
                ✓ {item.label}
              </div>
            ))}
          </div>
        )}

        {/* Error message */}
        {status === "error" && step.error && (
          <div style={{ fontSize: 12, color: COLORS.error, marginBottom: 8, padding: "4px 8px", background: COLORS.error + "11", borderRadius: 6 }}>
            ✗ {step.error}
          </div>
        )}

        {/* Action row */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
          <button
            onClick={handleAction}
            style={{
              flex: 1,
              padding: "7px 14px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: 600,
              background: isRunning ? COLORS.error + "cc" : COLORS.accent,
              color: "#fff",
              transition: "opacity 0.2s",
            }}
            onMouseEnter={(e) => (e.target.style.opacity = "0.85")}
            onMouseLeave={(e) => (e.target.style.opacity = "1")}
          >
            {isRunning ? "⏹ Stop" : "▶ Avvia"}
          </button>

          <button
            onClick={handleToggleExpand}
            style={{
              padding: "7px 10px",
              borderRadius: 8,
              border: `1px solid ${COLORS.border}`,
              background: "transparent",
              color: COLORS.textMuted,
              cursor: "pointer",
              fontSize: 13,
              transition: "color 0.2s, border-color 0.2s",
            }}
            onMouseEnter={(e) => {
              e.target.style.color = COLORS.text;
              e.target.style.borderColor = COLORS.accent;
            }}
            onMouseLeave={(e) => {
              e.target.style.color = COLORS.textMuted;
              e.target.style.borderColor = COLORS.border;
            }}
            title={expanded ? "Chiudi log" : "Apri log"}
          >
            {expanded ? "▼ Log" : "▶ Log"}
          </button>
        </div>

        {/* Expandable log panel */}
        {expanded && (
          <div className="log-panel">
            {displayLogs.length === 0 ? (
              <div style={{ color: COLORS.textMuted, fontStyle: "italic" }}>
                {isRunning ? "In attesa di log..." : "Nessun log disponibile"}
              </div>
            ) : (
              displayLogs.map((line, i) => {
                let cls = "log-line";
                if (line.toLowerCase().includes("error") || line.toLowerCase().includes("errore")) cls += " error-line";
                else if (line.toLowerCase().includes("warn")) cls += " warn-line";
                return (
                  <div key={i} className={cls}>
                    {line}
                  </div>
                );
              })
            )}
            <div ref={logEndRef} />
          </div>
        )}
      </div>
    </>
  );
}
