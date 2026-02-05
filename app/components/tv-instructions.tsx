import { useState, useEffect } from "react";
import { Info } from "lucide-react";

export function TVInstructions() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
    }, 5000);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "i" || e.key === "I") {
        setVisible((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      clearTimeout(timer);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  if (!visible) {
    return (
      <button
        onClick={() => setVisible(true)}
        className="fixed bottom-6 right-6 bg-zinc-800/80 hover:bg-zinc-700/80 text-white p-3 rounded-full transition-colors z-50"
      >
        <Info className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 bg-zinc-900/95 backdrop-blur-sm text-white p-6 rounded-lg shadow-2xl border border-zinc-700 z-50 max-w-md">
      <div className="flex items-start gap-3">
        <Info className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
        <div>
          <h3 className="font-semibold mb-3 text-lg">Remote Controls</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <span className="text-zinc-400">Arrow Keys:</span>
              <span>Navigate</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-zinc-400">Enter:</span>
              <span>Select</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-zinc-400">Backspace/Esc:</span>
              <span>Back</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-zinc-400">I:</span>
              <span>Toggle Help</span>
            </div>
          </div>
        </div>
        <button
          onClick={() => setVisible(false)}
          className="text-zinc-400 hover:text-white transition-colors"
        >
          ×
        </button>
      </div>
    </div>
  );
}
