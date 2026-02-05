import { Dashboard } from "../components/Dashboard";
import { LoadingScreen } from "../components/LoadingScreen";
import { LoginScreen } from "../components/LoginScreen";
import { UI_STATES, useSession } from "../state/session";

export function AppShell() {
  const { uiState, status, error, loginWithCredentials, triggerRefresh } = useSession();

  if (uiState === UI_STATES.BOOT) {
    return <LoadingScreen />;
  }

  if (uiState === UI_STATES.LOGGING_IN) {
    return <LoadingScreen title="Logging in" message="Validating credentials..." />;
  }

  if (uiState === UI_STATES.NOT_LOGGED_IN) {
    return (
      <LoginScreen
        onSubmit={loginWithCredentials}
        isSubmitting={uiState === UI_STATES.LOGGING_IN}
        error={error}
      />
    );
  }

  if (uiState === UI_STATES.REFRESHING) {
    return (
      <LoadingScreen
        title="Refreshing channels"
        message="We are rebuilding the IPTV cache. This can take a few moments."
      />
    );
  }

  if (!status) {
    return <LoadingScreen />;
  }

  return (
    <Dashboard
      status={status}
      onRefresh={triggerRefresh}
      isRefreshing={uiState === UI_STATES.REFRESHING}
      error={error}
    />
  );
}
