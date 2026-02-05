import { useEffect, useMemo, useState } from "react";
import {
  Channel,
  StatsResponse,
  StatusResponse,
  getChannels,
  getStats,
} from "../api/iptv";

const CATEGORY_TABS = ["tv", "movies", "series", "other"] as const;
const CATEGORY_LABELS: Record<(typeof CATEGORY_TABS)[number], string> = {
  tv: "TV",
  movies: "Movies",
  series: "Series",
  other: "Other",
};
const PAGE_SIZE = 24;
const SKELETON_COUNT = 8;
const SEARCH_DEBOUNCE_MS = 350;

const formatTimestamp = (value: string | null) => {
  if (!value) {
    return "Never";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

type DashboardProps = {
  status: StatusResponse;
  onRefresh: () => void;
  isRefreshing: boolean;
  error: string | null;
};

export function Dashboard({ status, onRefresh, isRefreshing, error }: DashboardProps) {
  const [category, setCategory] = useState<(typeof CATEGORY_TABS)[number]>("tv");
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [channels, setChannels] = useState<Channel[]>([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [channelsLoading, setChannelsLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [channelsError, setChannelsError] = useState<string | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
      setPage(1);
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(handle);
  }, [search]);

  useEffect(() => {
    setStatsLoading(true);
    getStats()
      .then((payload) => {
        setStats(payload);
        setStatsError(null);
      })
      .catch((err) => {
        const message = err instanceof Error ? err.message : "Unable to load stats.";
        setStatsError(message);
        setStats({ total: 0, tv: 0, movies: 0, series: 0, other: 0 });
      })
      .finally(() => setStatsLoading(false));
  }, [status.last_refresh]);

  useEffect(() => {
    setChannelsLoading(true);
    getChannels({
      page,
      page_size: PAGE_SIZE,
      search: debouncedSearch || undefined,
      category,
    })
      .then((payload) => {
        setChannels(payload.channels);
        setTotal(payload.total);
        setChannelsError(null);
      })
      .catch((err) => {
        const message = err instanceof Error ? err.message : "Unable to load channels.";
        setChannelsError(message);
        setChannels([]);
        setTotal(0);
      })
      .finally(() => setChannelsLoading(false));
  }, [category, debouncedSearch, page, status.last_refresh]);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total]);

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-semibold">IPTV Dashboard</h1>
          <p className="text-slate-400">
            Last refresh: {formatTimestamp(status.last_refresh)} · Channels: {status.channel_count}
          </p>
        </div>
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="rounded-lg bg-indigo-500 px-4 py-2 font-semibold disabled:opacity-50"
        >
          {isRefreshing ? "Refreshing..." : "Refresh Cache"}
        </button>
      </header>

      {error ? (
        <div className="bg-red-500/10 border border-red-500/30 text-red-200 rounded-lg px-4 py-3 mb-6">
          {error}
        </div>
      ) : null}

      <section className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
        {(statsLoading ? Array.from({ length: 5 }) : null)?.map((_, index) => (
          <div
            key={`stat-skeleton-${index}`}
            className="h-20 rounded-xl bg-slate-900 border border-slate-800 animate-pulse"
          />
        ))}
        {!statsLoading && stats ? (
          [
            { label: "Total", value: stats.total },
            { label: "TV", value: stats.tv },
            { label: "Movies", value: stats.movies },
            { label: "Series", value: stats.series },
            { label: "Other", value: stats.other },
          ].map((item) => (
            <div
              key={item.label}
              className="rounded-xl bg-slate-900 border border-slate-800 px-4 py-3"
            >
              <p className="text-slate-400 text-sm">{item.label}</p>
              <p className="text-2xl font-semibold">{item.value}</p>
            </div>
          ))
        ) : null}
        {statsError ? (
          <p className="text-slate-400 md:col-span-5">{statsError}</p>
        ) : null}
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div className="flex flex-wrap gap-2">
            {CATEGORY_TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setCategory(tab);
                  setPage(1);
                }}
                className={`px-4 py-2 rounded-lg border ${
                  category === tab
                    ? "bg-indigo-500 border-indigo-400 text-white"
                    : "border-slate-700 text-slate-300 hover:border-slate-500"
                }`}
              >
                {CATEGORY_LABELS[tab]}
              </button>
            ))}
          </div>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search channels"
            className="w-full md:max-w-xs rounded-lg bg-slate-950 border border-slate-800 px-3 py-2"
          />
        </div>

        {channelsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {Array.from({ length: SKELETON_COUNT }).map((_, index) => (
              <div
                key={`channel-skeleton-${index}`}
                className="h-20 rounded-xl bg-slate-950 border border-slate-800 animate-pulse"
              />
            ))}
          </div>
        ) : channels.length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {channels.map((channel) => (
              <div
                key={`${channel.name}-${channel.url}`}
                className="rounded-xl border border-slate-800 bg-slate-950 px-4 py-3"
              >
                <p className="font-semibold truncate">{channel.name}</p>
                <p className="text-sm text-slate-400 truncate">{channel.group}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-slate-400 py-12">
            <p className="text-lg font-semibold">No channels yet.</p>
            <p className="text-sm">
              If you just logged in, keep this screen open while the cache refreshes.
            </p>
          </div>
        )}

        {channelsError ? <p className="text-slate-400 mt-4">{channelsError}</p> : null}

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mt-6">
          <p className="text-sm text-slate-400">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page <= 1}
              className="px-3 py-2 rounded-lg border border-slate-700 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={page >= totalPages}
              className="px-3 py-2 rounded-lg border border-slate-700 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
