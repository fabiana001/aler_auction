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

export async function searchAuctions(query, params = {}) {
  const { data } = await api.get("/auctions/search", { params: { q: query, ...params } });
  return data;
}

export async function fetchNearby(lat, lng, radius, category) {
  const params = { lat, lng, radius };
  if (category) params.category = category;
  const { data } = await api.get("/auctions/nearby", { params });
  return data;
}

export async function fetchTrend(lat, lng, radius) {
  const { data } = await api.get("/auctions/trend", { params: { lat, lng, radius } });
  return data;
}

export async function fetchUpcoming(days = 365) {
  const { data } = await api.get("/auctions/upcoming", { params: { days } });
  return data;
}

export async function fetchActiveAuction() {
  const { data } = await api.get("/auctions/active-auction");
  return data;
}
