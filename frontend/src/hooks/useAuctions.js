import { useState, useEffect, useCallback } from "react";
import { fetchAuctions } from "../utils/api";

export function useAuctions() {
  const [auctions, setAuctions] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async (params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAuctions(params);
      setAuctions(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err.message || "Failed to load auctions");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { auctions, total, loading, error, reload: load };
}
