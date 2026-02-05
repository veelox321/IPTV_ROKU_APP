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
