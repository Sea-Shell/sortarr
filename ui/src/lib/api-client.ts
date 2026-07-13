import axios, { AxiosError, type AxiosInstance } from 'axios';

/**
 * API error response structure
 */
export interface ApiError {
  message: string;
  code?: string;
  details?: unknown;
}

/**
 * Get base URL from environment or default to relative paths
 * Since UI and API are served from same origin, use relative URLs
 */
const getBaseURL = (): string => {
  return import.meta.env.VITE_API_BASE_URL || '';
};

/**
 * Create axios instance with base configuration
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: getBaseURL(),
    timeout: 30000, // 30 second timeout
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true, // Include cookies for auth
  });

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add any auth tokens or custom headers here if needed
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response) => {
      return response;
    },
    (error: AxiosError<ApiError>) => {
      // Handle common error cases
      if (error.response) {
        // Server responded with error status
        const apiError: ApiError = {
          message: error.response.data?.message || error.message,
          code: error.response.data?.code,
          details: error.response.data?.details,
        };
        return Promise.reject(apiError);
      } else if (error.request) {
        // Request made but no response received
        return Promise.reject({
          message: 'No response from server. Please check your connection.',
          code: 'NETWORK_ERROR',
        } as ApiError);
      } else {
        // Something else happened
        return Promise.reject({
          message: error.message || 'An unexpected error occurred',
          code: 'UNKNOWN_ERROR',
        } as ApiError);
      }
    }
  );

  return client;
};

/**
 * Singleton API client instance
 */
export const apiClient = createApiClient();

/**
 * Helper to check if error is an API error
 */
export const isApiError = (error: unknown): error is ApiError => {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as ApiError).message === 'string'
  );
};
