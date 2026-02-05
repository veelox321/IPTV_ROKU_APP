import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { getStatus, login, refresh } from "../api/iptv";
import type { StatusResponse } from "../api/types";

type SessionPhase =
  | "BOOT"
  | "CHECK_STATUS"
  | "NOT_LOGGED_IN"
  | "LOGGED_IN"
  | "REFRESHING"
  | "READY";

type Credentials = {
  host: string;
  username: string;
  password: string;
};

type SessionContextValue = {
  phase: SessionPhase;
  status: StatusResponse | null;
  error: string | null;
  login: (credentials: Credentials) => Promise<void>;
  refresh: () => Promise<void>;
  checkStatus: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

function resolvePhase(status: StatusResponse): SessionPhase {
  if (!status.logged_in) {
    return "NOT_LOGGED_IN";
  }
  if (status.refreshing) {
    return "REFRESHING";
  }
  return "READY";
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<SessionPhase>("BOOT");
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);

  const checkStatus = useCallback(async () => {
    if (inFlight.current) {
      return;
    }
    inFlight.current = true;
    setPhase((prev) => (prev === "BOOT" ? "CHECK_STATUS" : prev));

    try {
      const payload = await getStatus();
      setStatus(payload);
      setPhase(resolvePhase(payload));
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load session.";
      setError(message);
      setPhase("NOT_LOGGED_IN");
    } finally {
      inFlight.current = false;
    }
  }, []);

  const handleLogin = useCallback(
    async (credentials: Credentials) => {
      setError(null);
      setPhase("CHECK_STATUS");
      try {
        await login(credentials);
        setPhase("LOGGED_IN");
        await handleRefresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Login failed.";
        setError(message);
        setPhase("NOT_LOGGED_IN");
      }
    },
    []
  );

  const handleRefresh = useCallback(async () => {
    setError(null);
    setPhase("REFRESHING");
    try {
      await refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Refresh failed.";
      setError(message);
    } finally {
      await checkStatus();
    }
  }, [checkStatus]);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  useEffect(() => {
    if (phase !== "REFRESHING") {
      return undefined;
    }

    const interval = window.setInterval(() => {
      void checkStatus();
    }, 2000);

    return () => window.clearInterval(interval);
  }, [checkStatus, phase]);

  const value = useMemo(
    () => ({
      phase,
      status,
      error,
      login: handleLogin,
      refresh: handleRefresh,
      checkStatus,
    }),
    [phase, status, error, handleLogin, handleRefresh, checkStatus]
  );

  return createElement(SessionContext.Provider, { value }, children);
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return context;
}
