import { useState, useEffect, useCallback, useRef } from "react";
import {
  fetchPipelineStatus,
  startStep,
  startAll,
  retryFromStep as retryFromStepApi,
  stopStep,
} from "../utils/pipelineApi";

const POLL_INTERVAL = 2000;

export function usePipeline() {
  const [steps, setSteps] = useState([]);
  const [running, setRunning] = useState(false);
  const [lastError, setLastError] = useState(null);
  const [connected, setConnected] = useState(false);
  const intervalRef = useRef(null);

  const pollStatus = useCallback(async () => {
    try {
      const data = await fetchPipelineStatus();
      setSteps(data.steps || []);
      setRunning(data.running || false);
      setConnected(true);
    } catch (err) {
      setConnected(false);
      setLastError(err.message || "Failed to fetch pipeline status");
    }
  }, []);

  useEffect(() => {
    pollStatus();
    intervalRef.current = setInterval(pollStatus, POLL_INTERVAL);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [pollStatus]);

  const runStep = useCallback(async (stepId) => {
    try {
      await startStep(stepId);
      pollStatus();
    } catch (err) {
      setLastError(err.message || `Failed to run step ${stepId}`);
    }
  }, [pollStatus]);

  const runAll = useCallback(async (fromStep) => {
    try {
      await startAll(fromStep);
      pollStatus();
    } catch (err) {
      setLastError(err.message || "Failed to run pipeline");
    }
  }, [pollStatus]);

  const retryFromStep = useCallback(async (stepId) => {
    try {
      await retryFromStepApi(stepId);
      pollStatus();
    } catch (err) {
      setLastError(err.message || `Failed to retry from step ${stepId}`);
    }
  }, [pollStatus]);

  const stop = useCallback(async (stepId) => {
    try {
      await stopStep(stepId);
      pollStatus();
    } catch (err) {
      setLastError(err.message || `Failed to stop step ${stepId}`);
    }
  }, [pollStatus]);

  return {
    steps,
    running,
    lastError,
    runStep,
    runAll,
    retryFromStep,
    stopStep: stop,
    connected,
  };
}
