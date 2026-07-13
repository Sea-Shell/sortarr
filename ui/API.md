# API Integration Guide

## Overview

This UI uses TanStack Query (React Query) for data fetching and state management, with axios for HTTP requests.

## Configuration

Set the backend API URL via environment variable:

```bash
# Create .env file (see .env.example)
VITE_API_BASE_URL=http://localhost:8080
```

Default: `http://localhost:8080`

## Usage

Import hooks from `src/hooks/use-api.ts`:

```tsx
import { useHealth, usePipelines, useStats } from '@/hooks/use-api';

function Dashboard() {
  const { data: health, isLoading } = useHealth();
  const { data: pipelines } = usePipelines();
  const { data: stats } = useStats();
  
  if (isLoading) return <div>Loading...</div>;
  
  return (
    <div>
      <p>Status: {health?.status}</p>
      <p>Pipelines: {pipelines?.length}</p>
      <p>Total runs: {stats?.total_runs}</p>
    </div>
  );
}
```

## Available Hooks

### Queries (useQuery)
- `useAuthStatus()` - Check authentication status
- `useHealth()` - Health check
- `useConfig()` - Get configuration
- `usePipelines()` - List all pipelines
- `usePipeline(id)` - Get single pipeline
- `useSubscriptions()` - List subscriptions
- `useSubscriptionStats()` - Subscription statistics
- `useRuns()` - List all runs
- `useRun(id)` - Get single run
- `useRunDecisions(id)` - Get run decisions
- `useStats()` - Get statistics

### Mutations (useMutation)
- `useLogin()` - Login
- `useLogout()` - Logout
- `useUpdateConfig()` - Update configuration
- `useCreatePipeline()` - Create pipeline
- `useUpdatePipeline()` - Update pipeline
- `useDeletePipeline()` - Delete pipeline
- `useMockPreview()` - Mock preview
- `useCachePreview()` - Cache preview

## Configuration

Query defaults (in `src/lib/query-client.ts`):
- **staleTime**: 30 seconds (data considered fresh)
- **refetchInterval**: 30 seconds (polling interval)
- **retry**: 1 (retry failed requests once)

## Error Handling

All hooks return typed errors via `ApiError`:

```tsx
const { data, error } = useHealth();

if (error) {
  console.error(error.message); // User-friendly message
  console.error(error.code);    // Error code
  console.error(error.details); // Additional details
}
```

## DevTools

React Query DevTools are enabled in development mode. Press the floating button in the bottom-right corner to open.

## Examples

See `src/hooks/use-api.examples.tsx` for complete examples.
