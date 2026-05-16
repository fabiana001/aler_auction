import axios from "axios";

const API_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 10000,
});

export async function fetchAuctions(params = {}) {
  const { data } = await api.get("/auctions", { params });
  return data;
}

export async function fetchAuction(id) {
  const { data } = await api.get(`/auctions/${id}`);
  return data;
}
