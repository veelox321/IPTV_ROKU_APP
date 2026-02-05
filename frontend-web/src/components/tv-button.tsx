import { useEffect, useRef } from "react";

interface TVButtonProps {
  children: React.ReactNode;
  focused?: boolean;
  onFocus?: () => void;
  onClick?: () => void;
  className?: string;
}

export function TVButton({
  children,
  focused = false,
  onFocus,
  onClick,
  className = "",
}: TVButtonProps) {
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (focused && buttonRef.current) {
      buttonRef.current.focus();
    }
  }, [focused]);

  return (
    <button
      ref={buttonRef}
      onFocus={onFocus}
      onClick={onClick}
      className={`
        px-16 py-8 rounded-lg
        bg-zinc-800 text-white
        transition-all duration-200
        outline-none
        ${
          focused
            ? "scale-110 ring-4 ring-blue-500 bg-blue-600 shadow-xl shadow-blue-500/50"
            : "hover:bg-zinc-700"
        }
        ${className}
      `}
    >
      {children}
    </button>
  );
}
