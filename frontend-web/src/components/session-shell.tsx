import type { ComponentType } from "react";
import { SessionProvider } from "../state/session";
import { LoginOverlay } from "./login-overlay";

type SessionShellProps = {
  Screen: ComponentType;
};

export function SessionShell({ Screen }: SessionShellProps) {
  return (
    <SessionProvider>
      <Screen />
      <LoginOverlay />
    </SessionProvider>
  );
}
