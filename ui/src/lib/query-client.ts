import { QueryClient } from '@tanstack/react-query';

/**
 * Create and configure TanStack Query client
 * 
 * Default configuration:
 * - staleTime: 30s (data considered fresh for 30 seconds)
 * - refetchInterval: 30s (polling interval for active queries)
 * - retry: 1 (retry failed requests once)
 * - refetchOnWindowFocus: true (refetch when window regains focus)
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30 seconds
      refetchInterval: 30 * 1000, // 30 seconds polling
      retry: 1, // Retry failed requests once
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 0, // Don't retry mutations by default
    },
  },
});
