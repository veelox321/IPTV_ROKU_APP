import { useState } from "react";
import { useSession } from "../state/session";
import { Button } from "./ui/button";
import { Input } from "./ui/input";

export function LoginOverlay() {
  const { phase, login, error } = useSession();
  const [host, setHost] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const isVisible = phase === "NOT_LOGGED_IN";

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!host || !username || !password || submitting) {
      return;
    }
    setSubmitting(true);
    try {
      await login({ host, username, password });
    } finally {
      setSubmitting(false);
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-zinc-800 bg-zinc-950/95 p-8 shadow-2xl">
        <h2 className="text-3xl font-semibold text-white mb-2">Connect IPTV</h2>
        <p className="text-zinc-400 mb-6">
          Enter your IPTV host, username, and password to refresh channels.
        </p>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-200" htmlFor="iptv-host">
              Host
            </label>
            <Input
              id="iptv-host"
              value={host}
              onChange={(event) => setHost(event.target.value)}
              placeholder="http://provider.example"
              className="bg-zinc-900 border-zinc-700 text-white"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-200" htmlFor="iptv-username">
              Username
            </label>
            <Input
              id="iptv-username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="username"
              className="bg-zinc-900 border-zinc-700 text-white"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-200" htmlFor="iptv-password">
              Password
            </label>
            <Input
              id="iptv-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="password"
              className="bg-zinc-900 border-zinc-700 text-white"
            />
          </div>
          {error ? <p className="text-sm text-red-400">{error}</p> : null}
          <Button
            type="submit"
            disabled={submitting || !host || !username || !password}
            className="w-full text-lg"
          >
            {submitting ? "Connecting..." : "Login & Refresh"}
          </Button>
        </form>
      </div>
    </div>
  );
}
