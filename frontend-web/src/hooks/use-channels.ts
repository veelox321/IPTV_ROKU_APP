import { useEffect, useState } from "react";
import { Channel, getChannels } from "../services/api";

export function useChannels({
  category,
  search,
  pageSize = 60,
}: {
  category?: string;
  search?: string;
  pageSize?: number;
}) {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const fetchChannels = async () => {
      setLoading(true);
      try {
        const response = await getChannels({
          page: 1,
          page_size: pageSize,
          category,
          search: search?.trim() || undefined,
        });
        if (isMounted) {
          setChannels(response.channels);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Unable to load channels.");
          setChannels([]);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchChannels();

    return () => {
      isMounted = false;
    };
  }, [category, pageSize, search]);

  return { channels, error, loading };
}
