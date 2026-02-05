import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { TVButton } from "../components/tv-button";
import { TVInstructions } from "../components/tv-instructions";
import { Tv, Film, Clapperboard, Activity, Grid3x3, RefreshCw } from "lucide-react";

export function HomeScreen() {
  const navigate = useNavigate();
  const [focusedIndex, setFocusedIndex] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

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
        refreshChannels();
        break;
    }
  };

  const printStatus = () => {
    const status = {
      timestamp: new Date().toLocaleString(),
      system: "IPTV v1.0",
      resolution: "1920x1080",
      connection: "Online",
      channels: 20,
      movies: 20,
      series: 20,
      otherChannels: 20,
      uptime: "Connected",
      performance: "Optimal",
    };
    
    console.log("=== SYSTEM STATUS ===");
    console.log(JSON.stringify(status, null, 2));
    console.log("====================");
  };

  const refreshChannels = async () => {
    setIsRefreshing(true);
    console.log("=== REFRESHING CHANNELS ===");
    console.log("Fetching latest channel list...");
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const refreshData = {
      timestamp: new Date().toLocaleString(),
      liveChannels: 20,
      movies: 20,
      series: 20,
      otherChannels: 20,
      totalContent: 80,
      status: "Success",
      message: "All channels refreshed successfully"
    };
    
    console.log("Refresh completed:");
    console.log(JSON.stringify(refreshData, null, 2));
    console.log("===========================");
    
    setIsRefreshing(false);
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center p-12">
      <TVInstructions />
      <div className="max-w-7xl w-full">
        <h1 className="text-6xl font-bold text-white text-center mb-16">
          IPTV
        </h1>
        <div className="flex gap-12 justify-center items-center mb-16">
          <TVButton
            focused={focusedIndex === 0}
            onFocus={() => setFocusedIndex(0)}
            onClick={() => handleSelect(0)}
          >
            <div className="flex flex-col items-center gap-4">
              <Tv className="w-20 h-20" />
              <span className="text-3xl font-semibold">LIVE</span>
            </div>
          </TVButton>

          <TVButton
            focused={focusedIndex === 1}
            onFocus={() => setFocusedIndex(1)}
            onClick={() => handleSelect(1)}
          >
            <div className="flex flex-col items-center gap-4">
              <Film className="w-20 h-20" />
              <span className="text-3xl font-semibold">MOVIES</span>
            </div>
          </TVButton>

          <TVButton
            focused={focusedIndex === 2}
            onFocus={() => setFocusedIndex(2)}
            onClick={() => handleSelect(2)}
          >
            <div className="flex flex-col items-center gap-4">
              <Clapperboard className="w-20 h-20" />
              <span className="text-3xl font-semibold">SERIES</span>
            </div>
          </TVButton>

          <TVButton
            focused={focusedIndex === 3}
            onFocus={() => setFocusedIndex(3)}
            onClick={() => handleSelect(3)}
          >
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
              px-8 py-4 rounded-lg
              bg-zinc-800 text-white
              transition-all duration-200
              outline-none
              flex items-center gap-3
              ${
                focusedIndex === 4
                  ? "scale-105 ring-4 ring-green-500 bg-green-600 shadow-xl shadow-green-500/50"
                  : "hover:bg-zinc-700"
              }
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
              px-8 py-4 rounded-lg
              bg-zinc-800 text-white
              transition-all duration-200
              outline-none
              flex items-center gap-3
              ${
                focusedIndex === 5
                  ? "scale-105 ring-4 ring-blue-500 bg-blue-600 shadow-xl shadow-blue-500/50"
                  : "hover:bg-zinc-700"
              }
              ${isRefreshing ? "opacity-50 cursor-not-allowed" : ""}
            `}
          >
            <RefreshCw className={`w-6 h-6 ${isRefreshing ? "animate-spin" : ""}`} />
            <span className="text-xl font-medium">
              {isRefreshing ? "Refreshing..." : "Refresh Channels"}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}