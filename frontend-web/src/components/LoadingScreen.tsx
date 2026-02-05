type LoadingScreenProps = {
  title?: string;
  message?: string;
};

export function LoadingScreen({
  title = "Loading IPTV",
  message = "Fetching status from the backend...",
}: LoadingScreenProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
      <div className="text-center">
        <div className="mx-auto h-12 w-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <h1 className="text-2xl font-semibold mt-6">{title}</h1>
        <p className="text-slate-400 mt-2">{message}</p>
      </div>
    </div>
  );
}
