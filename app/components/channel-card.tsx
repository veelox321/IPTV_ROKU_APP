import { useEffect, useRef } from "react";
import { Tv } from "lucide-react";

interface ChannelCardProps {
  channelName: string;
  channelNumber: number;
  logoUrl?: string;
  focused?: boolean;
  onFocus?: () => void;
  onClick?: () => void;
}

export function ChannelCard({
  channelName,
  channelNumber,
  logoUrl,
  focused = false,
  onFocus,
  onClick,
}: ChannelCardProps) {
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
        aspect-video
        rounded-lg
        bg-zinc-800
        flex flex-col items-center justify-center
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
      <div className="flex flex-col items-center justify-center gap-3 p-4">
        {logoUrl ? (
          <img
            src={logoUrl}
            alt={channelName}
            className="w-16 h-16 object-contain"
          />
        ) : (
          <Tv className="w-16 h-16 text-zinc-400" />
        )}
        <div className="text-center">
          <div className="text-xs text-zinc-400">Ch {channelNumber}</div>
          <div className="text-sm font-medium text-white">{channelName}</div>
        </div>
      </div>
    </button>
  );
}
