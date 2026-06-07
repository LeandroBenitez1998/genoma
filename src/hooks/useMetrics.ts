import { useQuery } from '@tanstack/react-query';
import { fetchMetrics, type MetricsData } from '@/lib/api';

export function useMetrics() {
  return useQuery<MetricsData>({
    queryKey: ['metrics'],
    queryFn: fetchMetrics,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}
