import axios from "axios";

const API_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 10000,
});

export async function fetchPipelineStatus() {
  const { data } = await api.get("/pipeline/status");
  return data;
}

export async function startStep(stepId) {
  const { data } = await api.post(`/pipeline/run/${stepId}`);
  return data;
}

export async function startAll(fromStep) {
  const params = fromStep ? { from_step: fromStep } : {};
  const { data } = await api.post("/pipeline/run", null, { params });
  return data;
}

export async function retryFromStep(stepId) {
  const { data } = await api.post("/pipeline/run", null, {
    params: { from_step: stepId },
  });
  return data;
}

export async function stopStep(stepId) {
  const { data } = await api.post(`/pipeline/stop/${stepId}`);
  return data;
}

export function openLogStream(stepId, onLine) {
  const url = `${API_URL}/api/pipeline/logs/${stepId}`;
  const source = new EventSource(url);

  source.onmessage = (event) => {
    onLine(event.data);
  };

  source.onerror = () => {
    // EventSource will auto-reconnect; no action needed
  };

  return () => {
    source.close();
  };
}
