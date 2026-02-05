import { useState } from "react";
import { Credentials } from "../api/iptv";

const DEFAULT_HOST_PLACEHOLDER = "https://provider.example";

type LoginScreenProps = {
  onSubmit: (credentials: Credentials) => void;
  isSubmitting: boolean;
  error: string | null;
};

export function LoginScreen({ onSubmit, isSubmitting, error }: LoginScreenProps) {
  const [host, setHost] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const canSubmit = Boolean(host && username && password && !isSubmitting);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }
    onSubmit({ host, username, password });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl">
        <h1 className="text-3xl font-semibold mb-2">IPTV Login</h1>
        <p className="text-slate-400 mb-6">
          Enter your IPTV provider credentials to unlock channels.
        </p>
        {error ? (
          <div className="bg-red-500/10 border border-red-500/30 text-red-200 rounded-lg px-4 py-3 mb-4">
            {error}
          </div>
        ) : null}
        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block">
            <span className="text-sm text-slate-300">Host</span>
            <input
              className="mt-1 w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-white"
              placeholder={DEFAULT_HOST_PLACEHOLDER}
              value={host}
              onChange={(event) => setHost(event.target.value)}
            />
          </label>
          <label className="block">
            <span className="text-sm text-slate-300">Username</span>
            <input
              className="mt-1 w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-white"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>
          <label className="block">
            <span className="text-sm text-slate-300">Password</span>
            <input
              type="password"
              className="mt-1 w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-white"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full rounded-lg bg-indigo-500 text-white px-4 py-3 font-semibold disabled:opacity-50"
          >
            {isSubmitting ? "Signing in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}
