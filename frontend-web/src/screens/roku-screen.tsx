import { useEffect, useMemo, useState } from "react";
import {
  getRokuContent,
  getRokuStatus,
  refreshChannels,
  type RokuContentItem,
  type RokuContentResponse,
  type RokuStatusResponse,
} from "../services/api";

const tabs = ["Live TV", "Movies", "Series", "Status", "Refresh"] as const;

type TabKey = (typeof tabs)[number];

type ContentState = {
  data: RokuContentResponse | null;
  loading: boolean;
  error: string | null;
};

const categoryMap: Record<TabKey, string | null> = {
  "Live TV": "tv",
  Movies: "movies",
  Series: "series",
  Status: null,
  Refresh: null,
};

const formatDate = (value: string | null) =>
  value ? new Date(value).toLocaleString() : "—";

export function RokuScreen() {
  const [activeTab, setActiveTab] = useState<TabKey>("Live TV");
  const [contentState, setContentState] = useState<ContentState>({
    data: null,
    loading: false,
    error: null,
  });
  const [statusState, setStatusState] = useState<{
    data: RokuStatusResponse | null;
    loading: boolean;
    error: string | null;
  }>({
    data: null,
    loading: false,
    error: null,
  });
  const [selectedItem, setSelectedItem] = useState<RokuContentItem | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const activeCategory = useMemo(() => categoryMap[activeTab], [activeTab]);

  useEffect(() => {
    if (!activeCategory) {
      return;
    }

    let isMounted = true;
    setContentState((prev) => ({ ...prev, loading: true, error: null }));

    getRokuContent(activeCategory)
      .then((payload) => {
        if (isMounted) {
          setContentState({ data: payload, loading: false, error: null });
        }
      })
      .catch((error) => {
        if (isMounted) {
          const message = error instanceof Error ? error.message : "Unable to load content.";
          setContentState({ data: null, loading: false, error: message });
        }
      });

    return () => {
      isMounted = false;
    };
  }, [activeCategory]);

  useEffect(() => {
    if (activeTab !== "Status") {
      return;
    }

    let isMounted = true;
    setStatusState((prev) => ({ ...prev, loading: true, error: null }));

    getRokuStatus()
      .then((payload) => {
        if (isMounted) {
          setStatusState({ data: payload, loading: false, error: null });
        }
      })
      .catch((error) => {
        if (isMounted) {
          const message = error instanceof Error ? error.message : "Unable to load status.";
          setStatusState({ data: null, loading: false, error: message });
        }
      });

    return () => {
      isMounted = false;
    };
  }, [activeTab]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshChannels();
      if (activeCategory) {
        const payload = await getRokuContent(activeCategory);
        setContentState({ data: payload, loading: false, error: null });
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <header className="flex items-center justify-between px-12 py-6 border-b border-zinc-800">
        <div className="flex items-center gap-6">
          <h1 className="text-3xl font-semibold">Futur IPTV</h1>
          <nav className="flex items-center gap-3">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                  activeTab === tab
                    ? "bg-white text-zinc-950 shadow"
                    : "bg-zinc-900 text-zinc-300 hover:text-white"
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <input
            placeholder="Search"
            className="bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button className="px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-sm">
            Genre
          </button>
          <button className="px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-sm">
            Sort: A–Z
          </button>
        </div>
      </header>

      <main className="px-12 py-8 space-y-8">
        {(activeTab === "Live TV" || activeTab === "Movies" || activeTab === "Series") && (
          <section className="space-y-6">
            {contentState.loading && (
              <div className="text-zinc-400">Loading {activeTab.toLowerCase()}…</div>
            )}
            {contentState.error && (
              <div className="text-red-400">{contentState.error}</div>
            )}
            {contentState.data?.rows.map((row) => (
              <div key={row.title} className="space-y-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold">{row.title}</h2>
                  <span className="text-sm text-zinc-400">{row.items.length} items</span>
                </div>
                <div className="flex gap-4 overflow-x-auto pb-2">
                  {row.items.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setSelectedItem(item)}
                      className="flex-shrink-0 w-48 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-blue-500 transition"
                    >
                      <div className="h-28 w-full rounded-t-xl bg-zinc-800 flex items-center justify-center">
                        {item.poster_url ? (
                          <img
                            src={item.poster_url}
                            alt={item.title}
                            className="h-full w-full object-cover rounded-t-xl"
                          />
                        ) : (
                          <span className="text-xs text-zinc-400">No poster</span>
                        )}
                      </div>
                      <div className="p-3 text-left">
                        <div className="text-sm font-semibold line-clamp-1">{item.title}</div>
                        <div className="text-xs text-zinc-400 line-clamp-1">{item.genre}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </section>
        )}

        {activeTab === "Status" && (
          <section className="max-w-3xl space-y-4">
            <h2 className="text-2xl font-semibold">System Status</h2>
            {statusState.loading && <div className="text-zinc-400">Loading status…</div>}
            {statusState.error && <div className="text-red-400">{statusState.error}</div>}
            {statusState.data && (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="text-sm text-zinc-400">Last Refresh</div>
                  <div className="text-lg font-semibold">
                    {formatDate(statusState.data.last_refresh)}
                  </div>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="text-sm text-zinc-400">Account Status</div>
                  <div className="text-lg font-semibold text-green-400">
                    {statusState.data.account_status}
                  </div>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="text-sm text-zinc-400">Channels</div>
                  <div className="text-lg font-semibold">{statusState.data.channels}</div>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="text-sm text-zinc-400">Movies</div>
                  <div className="text-lg font-semibold">{statusState.data.movies}</div>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="text-sm text-zinc-400">Series</div>
                  <div className="text-lg font-semibold">{statusState.data.series}</div>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
                  <div className="text-sm text-zinc-400">Playlists</div>
                  <div className="text-lg font-semibold">{statusState.data.total_playlists}</div>
                </div>
              </div>
            )}
          </section>
        )}

        {activeTab === "Refresh" && (
          <section className="space-y-4">
            <h2 className="text-2xl font-semibold">Refresh Playlists</h2>
            <p className="text-zinc-400">
              Keep your playlists up to date. While refreshing, playback and navigation are paused.
            </p>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={`px-6 py-3 rounded-xl text-sm font-semibold transition ${
                isRefreshing
                  ? "bg-blue-500/60 text-white"
                  : "bg-blue-500 text-white hover:bg-blue-400"
              }`}
            >
              {isRefreshing ? "Refreshing…" : "Refresh Now"}
            </button>
          </section>
        )}
      </main>

      {selectedItem && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center px-6">
          <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6 max-w-3xl w-full">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-2xl font-semibold">{selectedItem.title}</h3>
                <p className="text-sm text-zinc-400 mt-1">{selectedItem.genre}</p>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="text-zinc-400 hover:text-white"
              >
                Close
              </button>
            </div>
            <div className="mt-4 grid grid-cols-[200px,1fr] gap-6">
              <div className="h-48 bg-zinc-800 rounded-xl flex items-center justify-center">
                {selectedItem.poster_url ? (
                  <img
                    src={selectedItem.poster_url}
                    alt={selectedItem.title}
                    className="h-full w-full object-cover rounded-xl"
                  />
                ) : (
                  <span className="text-xs text-zinc-400">No poster</span>
                )}
              </div>
              <div className="space-y-3 text-sm text-zinc-200">
                <p>{selectedItem.description}</p>
                <div className="flex gap-4 text-zinc-400">
                  <span>Duration: {selectedItem.duration || "—"}</span>
                  <span>Rating: {selectedItem.rating || "—"}</span>
                </div>
                <button className="px-4 py-2 rounded-lg bg-green-500 text-white">
                  Play
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
