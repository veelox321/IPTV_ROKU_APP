import { useCallback, useEffect, useMemo, useState } from "react";
import { Credentials, StatusResponse, getStatus, login, refresh } from "../api/iptv";

const STATUS_POLL_INTERVAL_MS = 2000;

export const UI_STATES = {
  BOOT: "BOOT",
  NOT_LOGGED_IN: "NOT_LOGGED_IN",
  LOGGING_IN: "LOGGING_IN",
  REFRESHING: "REFRESHING",
  READY: "READY",
} as const;

export type UIState = (typeof UI_STATES)[keyof typeof UI_STATES];

export type SessionState = {
  uiState: UIState;
  status: StatusResponse | null;
  error: string | null;
  loginWithCredentials: (credentials: Credentials) => Promise<void>;
  triggerRefresh: () => Promise<void>;
  reloadStatus: () => Promise<void>;
};

const describeError = (error: unknown, fallback: string): string => {
  if (error instanceof Error) {
    return error.message || fallback;
  }
  return fallback;
};

export function useSession(): SessionState {
  const [uiState, setUiState] = useState<UIState>(UI_STATES.BOOT);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const applyStatus = useCallback((payload: StatusResponse) => {
    setStatus(payload);
    if (!payload.logged_in) {
      setUiState(UI_STATES.NOT_LOGGED_IN);
      return;
    }
    if (payload.refreshing) {
      setUiState(UI_STATES.REFRESHING);
      return;
    }
    if (!payload.cache_available) {
      setUiState(UI_STATES.REFRESHING);
      return;
    }
    setUiState(UI_STATES.READY);
  }, []);

  const reloadStatus = useCallback(async () => {
    const payload = await getStatus();
    applyStatus(payload);
  }, [applyStatus]);

  const ensureRefresh = useCallback(
    async (currentStatus: StatusResponse | null) => {
      if (!currentStatus?.logged_in) {
        return;
      }
      if (currentStatus.refreshing) {
        return;
      }
      await refresh();
    },
    []
  );

  const boot = useCallback(async () => {
    setUiState(UI_STATES.BOOT);
    try {
      const payload = await getStatus();
      setError(null);
      setStatus(payload);

      if (!payload.logged_in) {
        setUiState(UI_STATES.NOT_LOGGED_IN);
        return;
      }

      if (payload.refreshing) {
        setUiState(UI_STATES.REFRESHING);
        return;
      }

      if (!payload.cache_available) {
        // On boot, a logged-in session without cache should trigger a refresh.
        setUiState(UI_STATES.REFRESHING);
        await ensureRefresh(payload);
        return;
      }

      setUiState(UI_STATES.READY);
    } catch (err) {
      setError(describeError(err, "Unable to reach the backend."));
      setUiState(UI_STATES.NOT_LOGGED_IN);
    }
  }, [ensureRefresh]);

  const loginWithCredentials = useCallback(
    async (credentials: Credentials) => {
      setUiState(UI_STATES.LOGGING_IN);
      try {
        await login(credentials);
        const payload = await getStatus();
        setError(null);
        setStatus(payload);

        if (!payload.logged_in) {
          setUiState(UI_STATES.NOT_LOGGED_IN);
          return;
        }

        if (payload.refreshing) {
          setUiState(UI_STATES.REFRESHING);
          return;
        }

        if (!payload.cache_available) {
          setUiState(UI_STATES.REFRESHING);
          await ensureRefresh(payload);
          return;
        }

        setUiState(UI_STATES.READY);
      } catch (err) {
        setError(describeError(err, "Login failed."));
        setUiState(UI_STATES.NOT_LOGGED_IN);
      }
    },
    [ensureRefresh]
  );

  const triggerRefresh = useCallback(async () => {
    if (!status?.logged_in) {
      setError("Login is required before refreshing the cache.");
      setUiState(UI_STATES.NOT_LOGGED_IN);
      return;
    }

    try {
      setUiState(UI_STATES.REFRESHING);
      await refresh();
      await reloadStatus();
    } catch (err) {
      setError(describeError(err, "Refresh failed."));
      await reloadStatus();
    }
  }, [reloadStatus, status]);

  useEffect(() => {
    void boot();
  }, [boot]);

  useEffect(() => {
    if (uiState !== UI_STATES.REFRESHING) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      reloadStatus().catch(() => null);
    }, STATUS_POLL_INTERVAL_MS);

    return () => window.clearInterval(intervalId);
  }, [reloadStatus, uiState]);

  useEffect(() => {
    if (uiState === UI_STATES.READY || uiState === UI_STATES.REFRESHING) {
      setError(null);
    }
  }, [uiState]);

  return useMemo(
    () => ({
      uiState,
      status,
      error,
      loginWithCredentials,
      triggerRefresh,
      reloadStatus,
    }),
    [uiState, status, error, loginWithCredentials, triggerRefresh, reloadStatus]
  );
}
