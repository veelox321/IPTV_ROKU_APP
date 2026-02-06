import { useEffect, useMemo, useState } from "react";
import {
  getRokuContent,
  getRokuStatus,
  refreshChannels,
  type RokuContentItem,
  type RokuContentResponse,
  type RokuStatusResponse,
} from "../services/api";

const tabs = ["Live", "TV", "Movies", "Series"] as const;

type TabKey = (typeof tabs)[number];

type ContentState = {
  data: RokuContentResponse | null;
  loading: boolean;
  error: string | null;
};

type Account = {
  id: string;
  username: string;
  password: string;
  url: string;
};

type StatusState = {
  data: RokuStatusResponse | null;
  loading: boolean;
  error: string | null;
};

type Phase = "splash" | "accounts" | "add" | "home";

const categoryMap: Record<TabKey, string> = {
  Live: "tv",
  TV: "tv",
  Movies: "movies",
  Series: "series",
};

const formatDate = (value: string | null) =>
  value ? new Date(value).toLocaleString() : "—";

const storageKey = "iptv_accounts";

export function RokuScreen() {
  const [phase, setPhase] = useState<Phase>("splash");
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [activeAccount, setActiveAccount] = useState<Account | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>("Live");
  const [formState, setFormState] = useState({
    username: "",
    password: "",
    url: "",
  });
  const [contentState, setContentState] = useState<ContentState>({
    data: null,
    loading: false,
    error: null,
  });
  const [statusState, setStatusState] = useState<StatusState>({
    data: null,
    loading: false,
    error: null,
  });
  const [selectedItem, setSelectedItem] = useState<RokuContentItem | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const activeCategory = useMemo(() => categoryMap[activeTab], [activeTab]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setPhase("accounts");
    }, 2000);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as Account[];
        if (Array.isArray(parsed)) {
          setAccounts(parsed);
        }
      } catch {
        setAccounts([]);
      }
    }
  }, []);

  useEffect(() => {
    if (phase !== "home") {
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
  }, [activeCategory, phase]);

  useEffect(() => {
    if (phase !== "home") {
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
  }, [phase]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshChannels();
      if (activeCategory) {
        const payload = await getRokuContent(activeCategory);
        setContentState({ data: payload, loading: false, error: null });
      }
      const statusPayload = await getRokuStatus();
      setStatusState({ data: statusPayload, loading: false, error: null });
    } catch (error) {
      console.error(error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleSelectAccount = (account: Account) => {
    setActiveAccount(account);
    setPhase("home");
  };

  const handleSaveAccount = () => {
    if (!formState.username || !formState.password || !formState.url) {
      return;
    }
    const newAccount: Account = {
      id: `acct-${Date.now()}`,
      username: formState.username,
      password: formState.password,
      url: formState.url,
    };
    const nextAccounts = [...accounts, newAccount];
    setAccounts(nextAccounts);
    localStorage.setItem(storageKey, JSON.stringify(nextAccounts));
    setFormState({ username: "", password: "", url: "" });
    handleSelectAccount(newAccount);
  };

  const flattenedItems = useMemo(() => {
    if (!contentState.data?.rows) {
      return [];
    }
    return contentState.data.rows.flatMap((row) =>
      row.items.map((item) => ({
        ...item,
        category: row.title,
      })),
    );
  }, [contentState.data]);

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {phase === "splash" && (
        <div className="min-h-screen flex flex-col items-center justify-center gap-6">
          <h1 className="text-5xl font-semibold">IPTV</h1>
          <div className="flex items-center gap-3 text-zinc-400">
            <span className="h-3 w-3 rounded-full bg-blue-500 animate-pulse" />
            Chargement des comptes…
          </div>
        </div>
      )}

      {phase === "accounts" && (
        <div className="min-h-screen flex flex-col items-center justify-center px-8">
          <h1 className="text-4xl font-semibold mb-10">IPTV</h1>
          <div className="w-full max-w-4xl grid md:grid-cols-[2fr_1fr] gap-10">
            <div className="space-y-6">
              <h2 className="text-xl font-semibold">Choisissez un utilisateur</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                {accounts.map((account) => (
                  <button
                    key={account.id}
                    onClick={() => handleSelectAccount(account)}
                    className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4 text-left hover:border-blue-500 transition"
                  >
                    <div className="text-lg font-semibold">{account.username}</div>
                    <div className="text-xs text-zinc-400 mt-1">{account.url}</div>
                  </button>
                ))}
                {accounts.length === 0 && (
                  <div className="text-zinc-400 text-sm">
                    Aucun compte enregistré pour le moment.
                  </div>
                )}
              </div>
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 space-y-4">
              <h3 className="text-lg font-semibold">Nouveau compte</h3>
              <p className="text-sm text-zinc-400">
                Ajoutez un nouvel account IPTV et sauvegardez vos credentials.
              </p>
              <button
                onClick={() => setPhase("add")}
                className="w-full rounded-xl bg-white text-zinc-950 py-2 font-semibold"
              >
                Ajouter un compte
              </button>
            </div>
          </div>
        </div>
      )}

      {phase === "add" && (
        <div className="min-h-screen flex flex-col items-center justify-center px-8">
          <div className="w-full max-w-xl rounded-2xl border border-zinc-800 bg-zinc-900 p-8 space-y-6">
            <div>
              <h2 className="text-2xl font-semibold">Ajouter un account</h2>
              <p className="text-sm text-zinc-400">
                Entrez votre nom d’utilisateur, mot de passe et lien IPTV.
              </p>
            </div>
            <div className="space-y-4">
              <label className="block text-sm text-zinc-300">
                Nom d’utilisateur
                <input
                  value={formState.username}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, username: event.target.value }))
                  }
                  className="mt-2 w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </label>
              <label className="block text-sm text-zinc-300">
                Mot de passe
                <input
                  type="password"
                  value={formState.password}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, password: event.target.value }))
                  }
                  className="mt-2 w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </label>
              <label className="block text-sm text-zinc-300">
                Lien IPTV
                <input
                  value={formState.url}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, url: event.target.value }))
                  }
                  placeholder="https://example.com/playlist.m3u"
                  className="mt-2 w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </label>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleSaveAccount}
                className="flex-1 rounded-xl bg-blue-500 text-white py-2 font-semibold"
              >
                Enregistrer
              </button>
              <button
                onClick={() => setPhase("accounts")}
                className="flex-1 rounded-xl border border-zinc-700 py-2 text-zinc-300"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}

      {phase === "home" && (
        <>
          <header className="flex items-center justify-between px-12 py-6 border-b border-zinc-800">
            <div className="flex items-center gap-6">
              <h1 className="text-3xl font-semibold">IPTV</h1>
              <nav
                className={`flex items-center gap-3 ${isRefreshing ? "pointer-events-none opacity-60" : ""}`}
              >
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
            <div className="text-sm text-zinc-400">
              {activeAccount ? `Connecté: ${activeAccount.username}` : ""}
            </div>
          </header>

          <main className="px-12 py-8 grid gap-8 lg:grid-cols-[1fr_320px]">
            <section
              className={`space-y-4 ${isRefreshing ? "pointer-events-none opacity-60" : ""}`}
            >
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-semibold">{activeTab}</h2>
                <span className="text-sm text-zinc-400">
                  {flattenedItems.length} éléments
                </span>
              </div>
              {contentState.loading && (
                <div className="text-zinc-400">Chargement en cours…</div>
              )}
              {contentState.error && <div className="text-red-400">{contentState.error}</div>}
              <div className="space-y-2">
                {flattenedItems.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setSelectedItem(item)}
                    className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3 text-left hover:border-blue-500 transition"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{item.title}</div>
                        <div className="text-xs text-zinc-400">
                          {item.category} • {item.genre}
                        </div>
                      </div>
                      <span className="text-xs text-zinc-500">Voir</span>
                    </div>
                  </button>
                ))}
              </div>
            </section>

            <aside className="space-y-4 rounded-2xl border border-zinc-800 bg-zinc-900 p-6 h-fit">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Statut</h3>
                <button
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                  className={`text-xs font-semibold ${
                    isRefreshing
                      ? "text-blue-300 cursor-not-allowed"
                      : "text-blue-400 hover:text-blue-300"
                  }`}
                >
                  {isRefreshing ? "Refresh…" : "Refresh"}
                </button>
              </div>
              <div className="text-sm text-zinc-400">
                Dernier refresh:{" "}
                {statusState.loading ? "Chargement…" : formatDate(statusState.data?.last_refresh ?? null)}
              </div>
              {statusState.error && <div className="text-red-400 text-sm">{statusState.error}</div>}
              {statusState.data && (
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span>Compte</span>
                    <span className="text-green-400">{statusState.data.account_status}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Channels</span>
                    <span>{statusState.data.channels}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Movies</span>
                    <span>{statusState.data.movies}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Séries</span>
                    <span>{statusState.data.series}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Playlists</span>
                    <span>{statusState.data.total_playlists}</span>
                  </div>
                </div>
              )}
            </aside>
          </main>
        </>
      )}

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
