import { useEffect, useRef } from "react";
import { Search } from "lucide-react";

interface TVSearchBoxProps {
  value: string;
  onChange: (value: string) => void;
  focused?: boolean;
  onFocus?: () => void;
  placeholder?: string;
}

export function TVSearchBox({
  value,
  onChange,
  focused = false,
  onFocus,
  placeholder = "Search...",
}: TVSearchBoxProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (focused && inputRef.current) {
      inputRef.current.focus();
    }
  }, [focused]);

  return (
    <div
      className={`
        relative flex items-center
        bg-zinc-800 rounded-lg
        transition-all duration-200
        ${
          focused
            ? "ring-4 ring-blue-500 shadow-xl shadow-blue-500/50"
            : ""
        }
      `}
    >
      <Search className="w-6 h-6 text-zinc-400 ml-4" />
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={onFocus}
        placeholder={placeholder}
        className="
          flex-1 bg-transparent text-white text-xl
          px-4 py-4 outline-none
          placeholder:text-zinc-500
        "
      />
      {value && (
        <button
          onClick={() => onChange("")}
          className="text-zinc-400 hover:text-white px-4 transition-colors"
        >
          ×
        </button>
      )}
    </div>
  );
}
