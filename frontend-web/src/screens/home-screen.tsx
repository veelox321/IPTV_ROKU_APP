import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router";
import { TVButton } from "../components/tv-button";
import { TVInstructions } from "../components/tv-instructions";
import { Tv, Film, Clapperboard, Activity, Grid3x3, RefreshCw } from "lucide-react";
import { getStats, getStatus, refreshChannels } from "../services/api";

const EXPECTED_REFRESH_SECONDS = 45;
const STUCK_THRESHOLD_SECONDS = 120;

export function HomeScreen() {
  const navigate = useNavigate();
  const [focusedIndex, setFocusedIndex] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshStartedAt, setRefreshStartedAt] = useState<string | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [status, setStatus] = useState<{
    loggedIn: boolean;
    refreshing: boolean;
    channelCount: number;
    lastRefresh: string | null;
    refreshStatus: string;
    refreshStartedAt: string | null;
    lastError: string | null;
  } | null>(null);
  const [stats, setStats] = useState<{
    total: number;
    tv: number;
    movies: number;
    series: number;
    other: number;
  } | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const refreshProgress = useMemo(() => {
    if (!isRefreshing) return 0;
    return Math.min(95, Math.round((elapsedSeconds / EXPECTED_REFRESH_SECONDS) * 100));
  }, [elapsedSeconds, isRefreshing]);

  const refreshStateLabel = useMemo(() => {
    if (status?.refreshStatus === "failed") return "failed";
    if (!isRefreshing) return "idle";
    if (elapsedSeconds > STUCK_THRESHOLD_SECONDS) return "possibly stuck";
    if (elapsedSeconds < 2) return "pending";
    return "running";
  }, [elapsedSeconds, isRefreshing, status?.refreshStatus]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowLeft":
          e.preventDefault();
          if (focusedIndex < 4) {
            setFocusedIndex((prev) => Math.max(0, prev - 1));
          } else if (focusedIndex === 5) {
            setFocusedIndex(4);
          }
          break;
        case "ArrowRight":
          e.preventDefault();
          if (focusedIndex < 4) {
            setFocusedIndex((prev) => Math.min(3, prev + 1));
          } else if (focusedIndex === 4) {
            setFocusedIndex(5);
          }
          break;
        case "ArrowDown":
          e.preventDefault();
          if (focusedIndex < 4) {
            setFocusedIndex(4);
          }
          break;
        case "ArrowUp":
          e.preventDefault();
          if (focusedIndex >= 4) {
            setFocusedIndex(0);
          }
          break;
        case "Enter":
          e.preventDefault();
          handleSelect(focusedIndex);
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [focusedIndex]);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const [statusPayload, statsPayload] = await Promise.all([getStatus(), getStats()]);
        setStatus({
          loggedIn: statusPayload.logged_in,
          refreshing: statusPayload.refreshing,
          channelCount: statusPayload.channel_count,
          lastRefresh: statusPayload.last_refresh,
          refreshStatus: statusPayload.refresh_status,
          refreshStartedAt: statusPayload.refresh_started_at,
          lastError: statusPayload.last_error,
        });
        setIsRefreshing(statusPayload.refreshing);
        setRefreshStartedAt(statusPayload.refresh_started_at);
        setStats({
          total: statsPayload.total,
          tv: statsPayload.tv,
          movies: statsPayload.movies,
          series: statsPayload.series,
          other: statsPayload.other,
        });
        setStatusError(null);
        setStatsError(null);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unable to fetch status.";
        setStatusError(message);
        setStatsError(message);
      }
    };

    loadStatus();
  }, []);

  useEffect(() => {
    if (!isRefreshing) {
      setElapsedSeconds(0);
      return;
    }

    const tick = window.setInterval(() => {
      if (!refreshStartedAt) {
        setElapsedSeconds((prev) => prev + 1);
        return;
      }
      const started = Date.parse(refreshStartedAt);
      if (Number.isNaN(started)) {
        setElapsedSeconds((prev) => prev + 1);
        return;
      }
      setElapsedSeconds(Math.max(0, Math.floor((Date.now() - started) / 1000)));
    }, 1000);

    return () => window.clearInterval(tick);
  }, [isRefreshing, refreshStartedAt]);

  useEffect(() => {
    if (!isRefreshing) return;

    const poll = window.setInterval(async () => {
      try {
        const statusPayload = await getStatus();
        setStatus((prev) => ({
          loggedIn: statusPayload.logged_in,
          refreshing: statusPayload.refreshing,
          channelCount: statusPayload.channel_count,
          lastRefresh: statusPayload.last_refresh,
          refreshStatus: statusPayload.refresh_status,
          refreshStartedAt: statusPayload.refresh_started_at,
          lastError: statusPayload.last_error,
        }));
        setRefreshStartedAt(statusPayload.refresh_started_at);

        if (!statusPayload.refreshing) {
          setIsRefreshing(false);
          const statsPayload = await getStats();
          setStats({
            total: statsPayload.total,
            tv: statsPayload.tv,
            movies: statsPayload.movies,
            series: statsPayload.series,
            other: statsPayload.other,
          });
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unable to poll refresh status.";
        setStatusError(message);
      }
    }, 2000);

    return () => window.clearInterval(poll);
  }, [isRefreshing]);

  const handleSelect = (index: number) => {
    switch (index) {
      case 0:
        navigate("/live");
        break;
      case 1:
        navigate("/movies");
        break;
      case 2:
        navigate("/series");
        break;
      case 3:
        navigate("/others");
        break;
      case 4:
        printStatus();
        break;
      case 5:
        refreshChannelsNow();
        break;
    }
  };

  const printStatus = () => {
    const statusPayload = {
      timestamp: new Date().toLocaleString(),
      loggedIn: status?.loggedIn ?? false,
      refreshing: status?.refreshing ?? false,
      refreshState: refreshStateLabel,
      refreshProgress,
      lastRefresh: status?.lastRefresh ?? "n/a",
      channels: status?.channelCount ?? 0,
      totals: stats ?? {
        total: 0,
        tv: 0,
        movies: 0,
        series: 0,
        other: 0,
      },
    };

    console.log("=== SYSTEM STATUS ===");
    console.log(JSON.stringify(statusPayload, null, 2));
    console.log("====================");
  };

  const refreshChannelsNow = async () => {
    setStatusError(null);
    console.log("=== REFRESHING CHANNELS ===");

    try {
      await refreshChannels();
      setIsRefreshing(true);
      setRefreshStartedAt(new Date().toISOString());
    } catch (error) {
      const message = error instanceof Error ? error.message : "Refresh failed.";
      setStatusError(message);
      setIsRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-12">
      <TVInstructions />
      <div className="max-w-7xl w-full">
        <h1 className="text-6xl font-bold text-white text-center mb-4">IPTV</h1>
        <p className="text-center text-zinc-400 text-xl mb-12">
          {statusError || statsError
            ? "Backend unreachable"
            : `Channels: ${stats?.total ?? 0} · Live: ${stats?.tv ?? 0} · Movies: ${
                stats?.movies ?? 0
              } · Series: ${stats?.series ?? 0}`}
        </p>
        <div className="flex gap-12 justify-center items-center mb-16">
          <TVButton focused={focusedIndex === 0} onFocus={() => setFocusedIndex(0)} onClick={() => handleSelect(0)}>
            <div className="flex flex-col items-center gap-4">
              <Tv className="w-20 h-20" />
              <span className="text-3xl font-semibold">LIVE</span>
            </div>
          </TVButton>

          <TVButton focused={focusedIndex === 1} onFocus={() => setFocusedIndex(1)} onClick={() => handleSelect(1)}>
            <div className="flex flex-col items-center gap-4">
              <Film className="w-20 h-20" />
              <span className="text-3xl font-semibold">MOVIES</span>
            </div>
          </TVButton>

          <TVButton focused={focusedIndex === 2} onFocus={() => setFocusedIndex(2)} onClick={() => handleSelect(2)}>
            <div className="flex flex-col items-center gap-4">
              <Clapperboard className="w-20 h-20" />
              <span className="text-3xl font-semibold">SERIES</span>
            </div>
          </TVButton>

          <TVButton focused={focusedIndex === 3} onFocus={() => setFocusedIndex(3)} onClick={() => handleSelect(3)}>
            <div className="flex flex-col items-center gap-4">
              <Grid3x3 className="w-20 h-20" />
              <span className="text-3xl font-semibold">OTHERS</span>
            </div>
          </TVButton>
        </div>

        <div className="flex justify-center gap-6">
          <button
            onFocus={() => setFocusedIndex(4)}
            onClick={() => handleSelect(4)}
            className={`
              px-8 py-4 rounded-lg bg-zinc-800 text-white transition-all duration-200 outline-none flex items-center gap-3
              ${focusedIndex === 4 ? "scale-105 ring-4 ring-green-500 bg-green-600 shadow-xl shadow-green-500/50" : "hover:bg-zinc-700"}
            `}
          >
            <Activity className="w-6 h-6" />
            <span className="text-xl font-medium">System Status</span>
          </button>

          <button
            onFocus={() => setFocusedIndex(5)}
            onClick={() => handleSelect(5)}
            disabled={isRefreshing}
            className={`
              px-8 py-4 rounded-lg bg-zinc-800 text-white transition-all duration-200 outline-none flex items-center gap-3
              ${focusedIndex === 5 ? "scale-105 ring-4 ring-blue-500 bg-blue-600 shadow-xl shadow-blue-500/50" : "hover:bg-zinc-700"}
              ${isRefreshing ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            <RefreshCw className={`w-6 h-6 ${isRefreshing ? "animate-spin" : ""}`} />
            <span className="text-xl font-medium">{isRefreshing ? "Refreshing..." : "Refresh Channels"}</span>
          </button>
        </div>

        <div className="mx-auto mt-8 max-w-2xl rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-300">Refresh state: {refreshStateLabel}</span>
            <span className="text-zinc-400">{isRefreshing ? `${elapsedSeconds}s` : "idle"}</span>
          </div>
          <div className="mt-2 h-2 w-full rounded-full bg-zinc-700 overflow-hidden">
            <div className="h-full bg-blue-500 transition-all duration-500" style={{ width: `${refreshProgress}%` }} />
          </div>
          {status?.lastError && <p className="mt-3 text-sm text-red-400">Last refresh error: {status.lastError}</p>}
        </div>
      </div>
    </div>
  );
}
