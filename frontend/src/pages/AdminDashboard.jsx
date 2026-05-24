import { useState, useCallback } from "react";
import { usePipeline } from "../hooks/usePipeline";
import StageCard from "../components/StageCard";

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

function AdminDashboard() {
  const { steps, running, lastError, runStep, runAll, retryFromStep, stopStep, connected } = usePipeline();
  const [toasts, setToasts] = useState([]);
  const [retryStepId, setRetryStepId] = useState(null);

  // Determine if any step has an error
  const errorStep = steps.find((s) => s.status === "error");
  const hasError = !!errorStep;

  // Find the step to retry from (last errored or first idle after done steps)
  const getRetryStepId = useCallback(() => {
    if (errorStep) return errorStep.id;
    const lastDone = [...steps].reverse().find((s) => s.status === "done");
    if (lastDone) {
      const idx = steps.findIndex((s) => s.id === lastDone.id);
      return steps[idx + 1]?.id || null;
    }
    return steps[0]?.id || null;
  }, [steps, errorStep]);

  const addToast = useCallback((message, type = "info") => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const handleRunAll = async () => {
    try {
      await runAll();
      addToast("Pipeline avviata", "success");
    } catch (err) {
      addToast(`Errore: ${err.message}`, "error");
    }
  };

  const handleRetry = async () => {
    const stepId = getRetryStepId();
    if (!stepId) return;
    setRetryStepId(stepId);
    try {
      await runAll(stepId);
      addToast(`Retry da step ${stepId}`, "info");
    } catch (err) {
      addToast(`Errore retry: ${err.message}`, "error");
    } finally {
      setRetryStepId(null);
    }
  };

  const handleStopAll = async () => {
    // Stop all running steps
    const runningSteps = steps.filter((s) => s.status === "running");
    for (const step of runningSteps) {
      try {
        await stopStep(step.id);
      } catch {
        // ignore individual stop errors
      }
    }
    addToast("Pipeline fermata", "info");
  };

  const handleRunStep = async (stepId) => {
    try {
      await runStep(stepId);
      addToast(`Step ${stepId} avviato`, "success");
    } catch (err) {
      addToast(`Errore: ${err.message}`, "error");
    }
  };

  const handleStopStep = async (stepId) => {
    try {
      await stopStep(stepId);
      addToast(`Step ${stepId} fermato`, "info");
    } catch (err) {
      addToast(`Errore: ${err.message}`, "error");
    }
  };

  const runningCount = steps.filter((s) => s.status === "running").length;
  const doneCount = steps.filter((s) => s.status === "done").length;
  const totalSteps = steps.length;

  return (
    <>
      <style>{`
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes fadeOut {
          from { opacity: 1; }
          to { opacity: 0; transform: translateY(-8px); }
        }
        .toast-enter {
          animation: slideInRight 0.3s ease;
        }
        .grid-responsive {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
        }
        @media (max-width: 1024px) {
          .grid-responsive {
            grid-template-columns: repeat(2, 1fr);
          }
        }
        @media (max-width: 640px) {
          .grid-responsive {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <div
        style={{
          minHeight: "100vh",
          background: COLORS.bg,
          color: COLORS.text,
          fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
        }}
      >
        {/* Header */}
        <header
          style={{
            background: COLORS.surface,
            borderBottom: `1px solid ${COLORS.border}`,
            padding: "16px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
            position: "sticky",
            top: 0,
            zIndex: 10,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>
              ⚙️ Pipeline Controller
            </h1>
            {/* Connection indicator */}
            <span
              style={{
                fontSize: 11,
                padding: "2px 8px",
                borderRadius: 10,
                background: connected ? COLORS.success + "22" : COLORS.error + "22",
                color: connected ? COLORS.success : COLORS.error,
                border: `1px solid ${connected ? COLORS.success : COLORS.error}44`,
              }}
            >
              {connected ? "● Connesso" : "● Disconnesso"}
            </span>
            {totalSteps > 0 && (
              <span style={{ fontSize: 13, color: COLORS.textMuted }}>
                {doneCount}/{totalSteps} completati
                {runningCount > 0 && (
                  <span style={{ color: COLORS.accent }}> · {runningCount} in corso</span>
                )}
              </span>
            )}
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button
              onClick={handleRunAll}
              style={{
                padding: "8px 16px",
                borderRadius: 8,
                border: "none",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
                background: COLORS.accent,
                color: "#fff",
                transition: "opacity 0.2s",
              }}
              onMouseEnter={(e) => (e.target.style.opacity = "0.85")}
              onMouseLeave={(e) => (e.target.style.opacity = "1")}
            >
              ▶ Run All
            </button>

            <button
              onClick={handleRetry}
              disabled={!hasError}
              style={{
                padding: "8px 16px",
                borderRadius: 8,
                border: `1px solid ${hasError ? COLORS.warning + "88" : COLORS.border}`,
                cursor: hasError ? "pointer" : "not-allowed",
                fontSize: 13,
                fontWeight: 600,
                background: hasError ? COLORS.warning + "22" : "transparent",
                color: hasError ? COLORS.warning : COLORS.textMuted,
                opacity: hasError ? 1 : 0.5,
                transition: "opacity 0.2s",
              }}
            >
              🔄 Retry da errore
            </button>

            <button
              onClick={handleStopAll}
              disabled={!running}
              style={{
                padding: "8px 16px",
                borderRadius: 8,
                border: `1px solid ${running ? COLORS.error + "88" : COLORS.border}`,
                cursor: running ? "pointer" : "not-allowed",
                fontSize: 13,
                fontWeight: 600,
                background: running ? COLORS.error + "22" : "transparent",
                color: running ? COLORS.error : COLORS.textMuted,
                opacity: running ? 1 : 0.5,
                transition: "opacity 0.2s",
              }}
            >
              ⏹ Stop All
            </button>
          </div>
        </header>

        {/* Error banner */}
        {hasError && errorStep && (
          <div
            style={{
              margin: "16px 24px 0",
              padding: "10px 16px",
              background: COLORS.error + "15",
              border: `1px solid ${COLORS.error}44`,
              borderRadius: 8,
              fontSize: 13,
              color: COLORS.error,
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span>✗</span>
            <strong>{errorStep.name || errorStep.id}</strong>
            {errorStep.error && ` — ${errorStep.error}`}
            <button
              onClick={handleRetry}
              style={{
                marginLeft: "auto",
                padding: "4px 10px",
                borderRadius: 6,
                border: `1px solid ${COLORS.error}66`,
                background: "transparent",
                color: COLORS.error,
                cursor: "pointer",
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              🔄 Retry
            </button>
          </div>
        )}

        {/* Steps grid */}
        <main style={{ padding: "20px 24px" }}>
          {steps.length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "60px 20px",
                color: COLORS.textMuted,
                fontSize: 14,
              }}
            >
              {connected
                ? "Nessuno step configurato. Avvia la pipeline per iniziare."
                : "Connessione al server in corso..."}
            </div>
          ) : (
            <div className="grid-responsive">
              {steps.map((step) => (
                <StageCard
                  key={step.id}
                  step={step}
                  onRun={handleRunStep}
                  onStop={handleStopStep}
                  onOpenLog={() => {}}
                />
              ))}
            </div>
          )}
        </main>

        {/* Toast notifications */}
        <div
          style={{
            position: "fixed",
            bottom: 20,
            right: 20,
            display: "flex",
            flexDirection: "column",
            gap: 8,
            zIndex: 1000,
          }}
        >
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className="toast-enter"
              style={{
                padding: "10px 16px",
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 500,
                minWidth: 220,
                maxWidth: 360,
                backdropFilter: "blur(8px)",
                background:
                  toast.type === "error"
                    ? "rgba(239, 68, 68, 0.25)"
                    : toast.type === "success"
                    ? "rgba(34, 197, 94, 0.25)"
                    : "rgba(108, 99, 255, 0.25)",
                border: `1px solid ${
                  toast.type === "error"
                    ? "rgba(239, 68, 68, 0.5)"
                    : toast.type === "success"
                    ? "rgba(34, 197, 94, 0.5)"
                    : "rgba(108, 99, 255, 0.5)"
                }`,
                color: COLORS.text,
                boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
              }}
            >
              {toast.type === "error" && "✗ "}
              {toast.type === "success" && "✓ "}
              {toast.type === "info" && "ℹ "}
              {toast.message}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

export default AdminDashboard;
