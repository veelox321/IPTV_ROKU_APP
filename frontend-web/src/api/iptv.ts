export type Credentials = {
  host: string;
  username: string;
  password: string;
};

export type Channel = {
  name: string;
  group: string;
  category: string;
  url: string;
  tvg_logo?: string;
  tvg_chno?: string;
};

export type ChannelResponse = {
  channels: Channel[];
  total: number;
  page: number;
  page_size: number;
  cached: boolean;
};

export type StatusResponse = {
  logged_in: boolean;
  refreshing: boolean;
  cache_available: boolean;
  last_refresh: string | null;
  channel_count: number;
};

export type StatsResponse = {
  total: number;
  tv: number;
  movies: number;
  series: number;
  other: number;
};

const DEFAULT_API_BASE_URL = "http://localhost:8000";
const REQUEST_TIMEOUT_MS = 15000;

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(
  /\/$/,
  ""
);

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
      },
      signal: controller.signal,
      ...options,
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `API ${response.status}: ${response.statusText}`);
    }

    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export async function login(credentials: Credentials): Promise<{ status: string }> {
  return requestJson<{ status: string }>("/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export async function refresh(): Promise<{ status: string }> {
  return requestJson<{ status: string }>("/refresh", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getStatus(): Promise<StatusResponse> {
  return requestJson<StatusResponse>("/status");
}

export async function getStats(): Promise<StatsResponse> {
  return requestJson<StatsResponse>("/stats");
}

export async function getChannels(params: {
  page: number;
  page_size: number;
  search?: string;
  category?: string;
  group?: string;
}): Promise<ChannelResponse> {
  const url = new URL(`${API_BASE_URL}/channels`);
  url.searchParams.set("page", params.page.toString());
  url.searchParams.set("page_size", params.page_size.toString());

  if (params.search) {
    url.searchParams.set("search", params.search);
  }
  if (params.category) {
    url.searchParams.set("category", params.category);
  }
  if (params.group) {
    url.searchParams.set("group", params.group);
  }

  const response = await fetch(url.toString());
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `API ${response.status}: ${response.statusText}`);
  }
  return (await response.json()) as ChannelResponse;
}
