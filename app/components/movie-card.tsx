import { useEffect, useRef } from "react";
import { Film } from "lucide-react";

interface MovieCardProps {
  title: string;
  posterUrl?: string;
  year?: number;
  focused?: boolean;
  onFocus?: () => void;
  onClick?: () => void;
}

export function MovieCard({
  title,
  posterUrl,
  year,
  focused = false,
  onFocus,
  onClick,
}: MovieCardProps) {
  const cardRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (focused && cardRef.current) {
      cardRef.current.focus();
      cardRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "nearest",
      });
    }
  }, [focused]);

  return (
    <button
      ref={cardRef}
      onFocus={onFocus}
      onClick={onClick}
      className={`
        relative
        rounded-lg
        bg-zinc-800
        transition-all duration-200
        outline-none
        overflow-hidden
        ${
          focused
            ? "scale-105 ring-4 ring-blue-500 shadow-xl shadow-blue-500/50 z-10"
            : "hover:bg-zinc-700"
        }
      `}
    >
      <div className="aspect-[2/3] relative">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-zinc-700">
            <Film className="w-16 h-16 text-zinc-500" />
          </div>
        )}
      </div>
      <div className="p-3 bg-zinc-900/90 absolute bottom-0 left-0 right-0">
        <div className="text-sm font-medium text-white truncate">{title}</div>
        {year && <div className="text-xs text-zinc-400">{year}</div>}
      </div>
    </button>
  );
}
