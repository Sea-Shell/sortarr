/**
 * Type definitions for Sortarr API
 */

// Auth types
export interface LoginRequest {
  password: string;
}

export interface AuthStatus {
  authenticated: boolean;
}

// Health types
export interface HealthResponse {
  status: string;
  authenticated: boolean;
  next_scheduled_run: string | null;
  pipelines_count: number;
  subscriptions_count: number;
  quota_used_today: number;
  quota_remaining: number;
}

// Config types
export interface Config {
  sonarr_url: string;
  radarr_url: string;
  sonarr_api_key?: string;
  radarr_api_key?: string;
  dry_run: boolean;
  backup_enabled: boolean;
  log_level: string;
  schedule?: string;
  ignore_list?: string[];
  [key: string]: unknown; // Allow additional config fields
}

// Pipeline types
export interface Pipeline {
  id: string;
  name: string;
  type: 'sonarr' | 'radarr';
  enabled: boolean;
  schedule?: string;
  filters: PipelineFilter[];
  created_at: string;
  updated_at: string;
}

export interface PipelineFilter {
  type: string;
  config: Record<string, unknown>;
  enabled: boolean;
}

export interface CreatePipelineRequest {
  name: string;
  type: 'sonarr' | 'radarr';
  enabled?: boolean;
  schedule?: string;
  filters?: PipelineFilter[];
}

export interface UpdatePipelineRequest extends Partial<CreatePipelineRequest> {
  id: string;
}

// Subscription types
export interface Subscription {
  id: string;
  pipeline_id: string;
  name: string;
  path: string;
  monitored: boolean;
  created_at: string;
}

export interface SubscriptionStats {
  total: number;
  monitored: number;
  by_pipeline: Record<string, number>;
}

// Run types
export interface Run {
  id: string;
  status: string;
  trigger: string;
  started_at: string | null;
  completed_at: string | null;
  subscriptions_fetched: number;
  activities_collected: number;
  videos_enriched: number;
  videos_inserted: number;
  videos_skipped: number;
  quota_used: number;
  error_message: string | null;
}

export interface Decision {
  run_id: string;
  pipeline_id: string;
  video_id: string;
  action: 'inserted' | 'skipped';
  filter_stage: string | null;
  filter_name: string | null;
  reason: string | null;
}

// Preview types
export interface PreviewRequest {
  pipeline_id: string;
  item_path: string;
}

export interface PreviewResponse {
  action: 'delete' | 'keep';
  reason: string;
  filter_name: string;
  item_path: string;
}

// Stats types
export interface Stats {
  pipelines_count: number;
  pipelines_enabled_count: number;
  subscriptions_count: number;
  activities_cached: number;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
}
