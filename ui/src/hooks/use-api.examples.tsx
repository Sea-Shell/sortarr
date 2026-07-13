/**
 * Example usage of API hooks
 * 
 * This file demonstrates how to use the typed API hooks in components.
 * Import the hooks you need from './hooks/use-api' and use them in your components.
 */

import { 
  useHealth, 
  useAuthStatus, 
  useLogin, 
  useConfig, 
  usePipelines,
  useStats 
} from './use-api';
import type { ApiError } from '../lib/api-client';
import type { AuthStatus } from '../lib/types';

/**
 * Example: Health check component
 */
export function HealthExample() {
  const { data, isLoading, error } = useHealth();
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return <div>Status: {data?.status}</div>;
}

/**
 * Example: Login form component
 */
export function LoginExample() {
  const { mutate: login, isPending } = useLogin({
    onSuccess: (data: AuthStatus) => {
      console.log('Login successful:', data);
    },
    onError: (error: ApiError) => {
      console.error('Login failed:', error.message);
    },
  });
  
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    login({ password: formData.get('password') as string });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input type="password" name="password" required />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}

/**
 * Example: Dashboard with multiple queries
 */
export function DashboardExample() {
  const { data: auth } = useAuthStatus();
  const { data: config } = useConfig();
  const { data: pipelines } = usePipelines();
  const { data: stats } = useStats();
  
  return (
    <div>
      <h1>Dashboard</h1>
      <p>Authenticated: {auth?.authenticated ? 'Yes' : 'No'}</p>
      <p>Pipelines: {pipelines?.length ?? 0}</p>
      <p>Total runs: {stats?.total_runs ?? 0}</p>
      <p>Dry run mode: {config?.dry_run ? 'On' : 'Off'}</p>
    </div>
  );
}
