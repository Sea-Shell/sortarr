import { useQuery, useMutation, useQueryClient, type UseQueryOptions, type UseMutationOptions } from '@tanstack/react-query';
import { apiClient, type ApiError } from '../lib/api-client';
import type {
  AuthStatus,
  LoginRequest,
  HealthResponse,
  Config,
  Pipeline,
  CreatePipelineRequest,
  UpdatePipelineRequest,
  Subscription,
  SubscriptionStats,
  Run,
  Decision,
  PreviewRequest,
  PreviewResponse,
  Stats,
} from '../lib/types';

/**
 * Query keys for cache management
 */
export const queryKeys = {
  auth: ['auth'] as const,
  health: ['health'] as const,
  config: ['config'] as const,
  pipelines: ['pipelines'] as const,
  pipeline: (id: string) => ['pipelines', id] as const,
  subscriptions: ['subscriptions'] as const,
  subscriptionStats: ['subscriptions', 'stats'] as const,
  runs: ['runs'] as const,
  run: (id: string) => ['runs', id] as const,
  runDecisions: (id: string) => ['runs', id, 'decisions'] as const,
  stats: ['stats'] as const,
};

// ============================================================================
// Auth Hooks
// ============================================================================

/**
 * Check authentication status
 */
export const useAuthStatus = (options?: UseQueryOptions<AuthStatus, ApiError>) => {
  return useQuery<AuthStatus, ApiError>({
    queryKey: queryKeys.auth,
    queryFn: async () => {
      const response = await apiClient.get<AuthStatus>('/api/auth/status');
      return response.data;
    },
    ...options,
  });
};

/**
 * Login mutation
 */
export const useLogin = (options?: UseMutationOptions<AuthStatus, ApiError, LoginRequest>) => {
  const queryClient = useQueryClient();
  
  return useMutation<AuthStatus, ApiError, LoginRequest>({
    mutationFn: async (data: LoginRequest) => {
      const response = await apiClient.post<AuthStatus>('/api/auth/login', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth });
    },
    ...options,
  });
};

/**
 * Logout mutation
 */
export const useLogout = (options?: UseMutationOptions<void, ApiError, void>) => {
  const queryClient = useQueryClient();
  
  return useMutation<void, ApiError, void>({
    mutationFn: async () => {
      await apiClient.post('/api/auth/logout');
    },
    onSuccess: () => {
      queryClient.clear();
    },
    ...options,
  });
};

// ============================================================================
// Health Hook
// ============================================================================

/**
 * Get health status
 */
export const useHealth = (options?: UseQueryOptions<HealthResponse, ApiError>) => {
  return useQuery<HealthResponse, ApiError>({
    queryKey: queryKeys.health,
    queryFn: async () => {
      const response = await apiClient.get<HealthResponse>('/api/health');
      return response.data;
    },
    ...options,
  });
};

// ============================================================================
// Config Hooks
// ============================================================================

/**
 * Get configuration
 */
export const useConfig = (options?: UseQueryOptions<Config, ApiError>) => {
  return useQuery<Config, ApiError>({
    queryKey: queryKeys.config,
    queryFn: async () => {
      const response = await apiClient.get<Config>('/api/config');
      return response.data;
    },
    ...options,
  });
};

/**
 * Update configuration
 */
export const useUpdateConfig = (options?: UseMutationOptions<Config, ApiError, Partial<Config>>) => {
  const queryClient = useQueryClient();
  
  return useMutation<Config, ApiError, Partial<Config>>({
    mutationFn: async (data: Partial<Config>) => {
      const response = await apiClient.put<Config>('/api/config', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.config });
    },
    ...options,
  });
};

// ============================================================================
// Pipeline Hooks
// ============================================================================

/**
 * Get all pipelines
 */
export const usePipelines = (options?: UseQueryOptions<Pipeline[], ApiError>) => {
  return useQuery<Pipeline[], ApiError>({
    queryKey: queryKeys.pipelines,
    queryFn: async () => {
      const response = await apiClient.get<Pipeline[]>('/api/pipelines');
      return response.data;
    },
    ...options,
  });
};

/**
 * Get single pipeline
 */
export const usePipeline = (id: string, options?: UseQueryOptions<Pipeline, ApiError>) => {
  return useQuery<Pipeline, ApiError>({
    queryKey: queryKeys.pipeline(id),
    queryFn: async () => {
      const response = await apiClient.get<Pipeline>(`/api/pipelines/${id}`);
      return response.data;
    },
    enabled: !!id,
    ...options,
  });
};

/**
 * Create pipeline
 */
export const useCreatePipeline = (options?: UseMutationOptions<Pipeline, ApiError, CreatePipelineRequest>) => {
  const queryClient = useQueryClient();
  
  return useMutation<Pipeline, ApiError, CreatePipelineRequest>({
    mutationFn: async (data: CreatePipelineRequest) => {
      const response = await apiClient.post<Pipeline>('/api/pipelines', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.pipelines });
    },
    ...options,
  });
};

/**
 * Update pipeline
 */
export const useUpdatePipeline = (options?: UseMutationOptions<Pipeline, ApiError, UpdatePipelineRequest>) => {
  const queryClient = useQueryClient();
  
  return useMutation<Pipeline, ApiError, UpdatePipelineRequest>({
    mutationFn: async (data: UpdatePipelineRequest) => {
      const response = await apiClient.put<Pipeline>(`/api/pipelines/${data.id}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.pipelines });
      queryClient.invalidateQueries({ queryKey: queryKeys.pipeline(data.id) });
    },
    ...options,
  });
};

/**
 * Delete pipeline
 */
export const useDeletePipeline = (options?: UseMutationOptions<void, ApiError, string>) => {
  const queryClient = useQueryClient();
  
  return useMutation<void, ApiError, string>({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/api/pipelines/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.pipelines });
    },
    ...options,
  });
};

// ============================================================================
// Subscription Hooks
// ============================================================================

/**
 * Get all subscriptions
 */
export const useSubscriptions = (options?: UseQueryOptions<Subscription[], ApiError>) => {
  return useQuery<Subscription[], ApiError>({
    queryKey: queryKeys.subscriptions,
    queryFn: async () => {
      const response = await apiClient.get<Subscription[]>('/api/subscriptions');
      return response.data;
    },
    ...options,
  });
};

/**
 * Get subscription statistics
 */
export const useSubscriptionStats = (options?: UseQueryOptions<SubscriptionStats, ApiError>) => {
  return useQuery<SubscriptionStats, ApiError>({
    queryKey: queryKeys.subscriptionStats,
    queryFn: async () => {
      const response = await apiClient.get<SubscriptionStats>('/api/subscriptions/stats');
      return response.data;
    },
    ...options,
  });
};

// ============================================================================
// Run Hooks
// ============================================================================

/**
 * Get all runs
 */
export const useRuns = (params?: { limit?: number }, options?: UseQueryOptions<Run[], ApiError>) => {
  return useQuery<Run[], ApiError>({
    queryKey: [...queryKeys.runs, params],
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (params?.limit) {
        queryParams.append('limit', params.limit.toString());
      }
      const url = `/api/runs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await apiClient.get<Run[]>(url);
      return response.data;
    },
    ...options,
  });
};

/**
 * Get single run
 */
export const useRun = (id: string, options?: UseQueryOptions<Run, ApiError>) => {
  return useQuery<Run, ApiError>({
    queryKey: queryKeys.run(id),
    queryFn: async () => {
      const response = await apiClient.get<Run>(`/api/runs/${id}`);
      return response.data;
    },
    enabled: !!id,
    ...options,
  });
};

/**
 * Get run decisions
 */
export const useRunDecisions = (id: string, params?: { limit?: number }, options?: UseQueryOptions<Decision[], ApiError>) => {
  return useQuery<Decision[], ApiError>({
    queryKey: [...queryKeys.runDecisions(id), params],
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (params?.limit) {
        queryParams.append('limit', params.limit.toString());
      }
      const url = `/api/runs/${id}/decisions${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await apiClient.get<Decision[]>(url);
      return response.data;
    },
    enabled: !!id,
    ...options,
  });
};

// ============================================================================
// Preview Hooks
// ============================================================================

/**
 * Mock preview mutation
 */
export const useMockPreview = (options?: UseMutationOptions<PreviewResponse, ApiError, PreviewRequest>) => {
  return useMutation<PreviewResponse, ApiError, PreviewRequest>({
    mutationFn: async (data: PreviewRequest) => {
      const response = await apiClient.post<PreviewResponse>('/api/preview/mock', data);
      return response.data;
    },
    ...options,
  });
};

/**
 * Cache preview mutation
 */
export const useCachePreview = (options?: UseMutationOptions<PreviewResponse, ApiError, PreviewRequest>) => {
  return useMutation<PreviewResponse, ApiError, PreviewRequest>({
    mutationFn: async (data: PreviewRequest) => {
      const response = await apiClient.post<PreviewResponse>('/api/preview/cache', data);
      return response.data;
    },
    ...options,
  });
};

// ============================================================================
// Stats Hook
// ============================================================================

/**
 * Get statistics
 */
export const useStats = (options?: UseQueryOptions<Stats, ApiError>) => {
  return useQuery<Stats, ApiError>({
    queryKey: queryKeys.stats,
    queryFn: async () => {
      const response = await apiClient.get<Stats>('/api/stats');
      return response.data;
    },
    ...options,
  });
};
