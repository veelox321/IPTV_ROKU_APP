import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { ChannelCard } from "../components/channel-card";
import { TVInstructions } from "../components/tv-instructions";
import { TVSearchBox } from "../components/tv-search-box";
import { ArrowLeft } from "lucide-react";
import { useChannels } from "../hooks/use-channels";

export function LiveScreen() {
  const navigate = useNavigate();
  const [focusedIndex, setFocusedIndex] = useState(-1); // Start at search box
  const [searchQuery, setSearchQuery] = useState("");
  const COLUMNS = 5;

  const { channels, error, loading } = useChannels({
    category: "tv",
    search: searchQuery,
    pageSize: 60,
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // If in search box
      if (focusedIndex === -1) {
        switch (e.key) {
          case "ArrowDown":
            e.preventDefault();
            if (channels.length > 0) {
              setFocusedIndex(0);
            }
            break;
          case "Backspace":
          case "Escape":
            if (!searchQuery) {
              e.preventDefault();
              navigate("/");
            }
            break;
        }
      } else {
        // In grid
        switch (e.key) {
          case "ArrowLeft":
            e.preventDefault();
            setFocusedIndex((prev) => Math.max(0, prev - 1));
            break;
          case "ArrowRight":
            e.preventDefault();
            setFocusedIndex((prev) => Math.min(channels.length - 1, prev + 1));
            break;
          case "ArrowUp":
            e.preventDefault();
            const newUpIndex = focusedIndex - COLUMNS;
            if (newUpIndex < 0) {
              setFocusedIndex(-1); // Back to search
            } else {
              setFocusedIndex(newUpIndex);
            }
            break;
          case "ArrowDown":
            e.preventDefault();
            setFocusedIndex((prev) =>
              Math.min(channels.length - 1, prev + COLUMNS)
            );
            break;
          case "Backspace":
          case "Escape":
            e.preventDefault();
            navigate("/");
            break;
          case "Enter":
            e.preventDefault();
            console.log("Selected channel:", channels[focusedIndex]);
            break;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [focusedIndex, searchQuery, channels, navigate]);

  return (
    <div className="min-h-screen bg-zinc-950 p-12">
      <TVInstructions />
      <div className="max-w-[1600px] mx-auto">
        <div className="flex items-center gap-6 mb-8">
          <button
            onClick={() => navigate("/")}
            className="text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-8 h-8" />
          </button>
          <h1 className="text-5xl font-bold text-white">Live Channels</h1>
        </div>

        <div className="mb-8">
          <TVSearchBox
            value={searchQuery}
            onChange={setSearchQuery}
            focused={focusedIndex === -1}
            onFocus={() => setFocusedIndex(-1)}
            placeholder="Search channels..."
          />
        </div>

        {loading ? (
          <div className="text-center text-zinc-400 text-2xl py-20">Loading…</div>
        ) : error ? (
          <div className="text-center text-red-400 text-2xl py-20">{error}</div>
        ) : channels.length > 0 ? (
          <div className="grid grid-cols-5 gap-6">
            {channels.map((channel, index) => (
              <ChannelCard
                key={`${channel.url}-${index}`}
                channelName={channel.name}
                channelNumber={Number.parseInt(channel.tvg_chno ?? "0", 10) || index + 1}
                logoUrl={channel.tvg_logo}
                focused={focusedIndex === index}
                onFocus={() => setFocusedIndex(index)}
                onClick={() =>
                  console.log("Clicked channel:", channels[focusedIndex])
                }
              />
            ))}
          </div>
        ) : (
          <div className="text-center text-zinc-500 text-2xl py-20">
            No channels found
          </div>
        )}
      </div>
    </div>
  );
}
