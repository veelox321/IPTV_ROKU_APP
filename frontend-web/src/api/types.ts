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
  refresh_started_at: string | null;
  refresh_status: "loading" | "success" | "failed" | "missing" | string;
  last_error: string | null;
  last_successful_refresh: string | null;
};

export type StatsResponse = {
  total: number;
  tv: number;
  movies: number;
  series: number;
  other: number;
};

export type RokuContentItem = {
  id: string;
  title: string;
  description: string;
  genre: string;
  category: string;
  stream_url: string;
  poster_url?: string | null;
  duration?: string | null;
  rating?: string | null;
};

export type RokuContentRow = {
  title: string;
  items: RokuContentItem[];
};

export type RokuContentResponse = {
  category: string;
  rows: RokuContentRow[];
  total_rows: number;
};

export type RokuStatusResponse = {
  last_refresh: string | null;
  channels: number;
  movies: number;
  series: number;
  episodes: number;
  total_playlists: number;
  account_status: string;
  refreshing: boolean;
  refresh_status: "loading" | "success" | "failed" | "missing" | string;
  refresh_started_at: string | null;
  last_error: string | null;
};
