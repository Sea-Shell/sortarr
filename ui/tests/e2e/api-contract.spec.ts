import { test, expect } from '@playwright/test';
import type {
  HealthResponse,
  Subscription,
  SubscriptionStats,
  Pipeline,
  Run,
  Config,
  Stats,
} from '../../src/lib/types';

/**
 * API Contract Tests
 * 
 * These tests validate that the API responses match the TypeScript type definitions.
 * They test against the real backend API (not mocked) to catch type mismatches,
 * missing fields, and incorrect data structures.
 * 
 * These tests would have caught:
 * - subscriptions using 'name' instead of 'channel_title'
 * - subscriptions using 'id' instead of 'subscription_id'
 * - stats returning object with 'by_pipeline' instead of array
 */

const API_BASE = process.env.API_BASE_URL || 'https://sortarr.bateau.cloud';

test.describe('API Contract Tests', () => {
  test.describe('Health Endpoint', () => {
    test('GET /api/health returns correct structure', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/health`);
      expect(response.ok()).toBeTruthy();
      
      const data: HealthResponse = await response.json();
      
      // Validate all required fields exist
      expect(data).toHaveProperty('status');
      expect(data).toHaveProperty('authenticated');
      expect(data).toHaveProperty('next_scheduled_run');
      expect(data).toHaveProperty('pipelines_count');
      expect(data).toHaveProperty('subscriptions_count');
      expect(data).toHaveProperty('quota_used_today');
      expect(data).toHaveProperty('quota_remaining');
      
      // Validate types
      expect(typeof data.status).toBe('string');
      expect(typeof data.authenticated).toBe('boolean');
      expect(typeof data.pipelines_count).toBe('number');
      expect(typeof data.subscriptions_count).toBe('number');
      expect(typeof data.quota_used_today).toBe('number');
      expect(typeof data.quota_remaining).toBe('number');
      
      // next_scheduled_run can be string or null
      if (data.next_scheduled_run !== null) {
        expect(typeof data.next_scheduled_run).toBe('string');
      }
    });
  });

  test.describe('Subscriptions Endpoints', () => {
    test('GET /api/subscriptions returns array with correct field names', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/subscriptions`);
      expect(response.ok()).toBeTruthy();
      
      const data: Subscription[] = await response.json();
      
      // MUST be array
      expect(Array.isArray(data)).toBeTruthy();
      
      if (data.length > 0) {
        const sub = data[0];
        
        // Check CORRECT field names (these bugs were in production)
        expect(sub).toHaveProperty('subscription_id');
        expect(sub).toHaveProperty('channel_title');
        expect(sub).toHaveProperty('channel_id');
        
        // These WRONG field names should NOT exist
        expect(sub).not.toHaveProperty('name'); // Wrong! Should be channel_title
        expect(sub).not.toHaveProperty('id'); // Wrong! Should be subscription_id
        
        // Validate types
        expect(typeof sub.subscription_id).toBe('string');
        expect(typeof sub.channel_id).toBe('string');
        expect(typeof sub.channel_title).toBe('string');
      }
    });

    test('GET /api/subscriptions handles null/undefined channel_title', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/subscriptions`);
      expect(response.ok()).toBeTruthy();
      
      const data: Subscription[] = await response.json();
      
      // All subscriptions should have channel_title (even if empty string)
      data.forEach(sub => {
        expect(sub).toHaveProperty('channel_title');
        expect(typeof sub.channel_title).toBe('string');
      });
    });

    test('GET /api/subscriptions/stats returns ARRAY not object', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/subscriptions/stats`);
      expect(response.ok()).toBeTruthy();
      
      const data: SubscriptionStats = await response.json();
      
      // CRITICAL: Must be array, not object with by_pipeline
      // This bug caused production 500 errors
      expect(Array.isArray(data)).toBeTruthy();
      
      // Should NOT have by_pipeline property (that was the bug)
      expect(data).not.toHaveProperty('by_pipeline');
      
      if (data.length > 0) {
        const stat = data[0];
        
        // Validate required fields
        expect(stat).toHaveProperty('subscription_id');
        expect(stat).toHaveProperty('channel_title');
        expect(stat).toHaveProperty('activities_count');
        expect(stat).toHaveProperty('last_fetched_at');
        
        // Validate types
        expect(typeof stat.subscription_id).toBe('string');
        expect(typeof stat.channel_title).toBe('string');
        expect(typeof stat.activities_count).toBe('number');
        
        // last_fetched_at can be string or null
        if (stat.last_fetched_at !== null) {
          expect(typeof stat.last_fetched_at).toBe('string');
        }
      }
    });
  });

  test.describe('Pipelines Endpoints', () => {
    test('GET /api/pipelines returns array with correct structure', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/pipelines`);
      expect(response.ok()).toBeTruthy();
      
      const data: Pipeline[] = await response.json();
      
      // Must be array
      expect(Array.isArray(data)).toBeTruthy();
      
      if (data.length > 0) {
        const pipeline = data[0];
        
        // Validate required fields
        expect(pipeline).toHaveProperty('id');
        expect(pipeline).toHaveProperty('name');
        expect(pipeline).toHaveProperty('enabled');
        expect(pipeline).toHaveProperty('order');
        
        // Validate types
        expect(typeof pipeline.id).toBe('string');
        expect(typeof pipeline.name).toBe('string');
        expect(typeof pipeline.enabled).toBe('boolean');
        expect(typeof pipeline.order).toBe('number');
      }
    });
  });

  test.describe('Runs Endpoints', () => {
    test('GET /api/runs returns array with correct structure', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/runs`);
      expect(response.ok()).toBeTruthy();
      
      const data: Run[] = await response.json();
      
      // Must be array
      expect(Array.isArray(data)).toBeTruthy();
      
      if (data.length > 0) {
        const run = data[0];
        
        // Validate required fields
        expect(run).toHaveProperty('id');
        expect(run).toHaveProperty('status');
        expect(run).toHaveProperty('trigger');
        expect(run).toHaveProperty('subscriptions_fetched');
        expect(run).toHaveProperty('videos_inserted');
        
        // Validate types
        expect(typeof run.id).toBe('string');
        expect(typeof run.status).toBe('string');
        expect(typeof run.trigger).toBe('string');
        expect(typeof run.subscriptions_fetched).toBe('number');
        expect(typeof run.videos_inserted).toBe('number');
      }
    });
  });

  test.describe('Config Endpoint', () => {
    test('GET /api/config returns correct structure', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/config`);
      expect(response.ok()).toBeTruthy();
      
      const data: Config = await response.json();
      
      // Validate required fields (actual fields returned by API)
      expect(data).toHaveProperty('schedule');
      expect(data).toHaveProperty('reprocess_days');
      expect(data).toHaveProperty('activity_limit');
      expect(data).toHaveProperty('subscription_limit');
      
      // Validate types
      if (data.schedule !== undefined) {
        expect(typeof data.schedule).toBe('string');
      }
      if (data.reprocess_days !== undefined) {
        expect(typeof data.reprocess_days).toBe('number');
      }
      if (data.activity_limit !== undefined) {
        expect(typeof data.activity_limit).toBe('number');
      }
      if (data.subscription_limit !== undefined) {
        expect(typeof data.subscription_limit).toBe('number');
      }
    });
  });

  test.describe('Stats Endpoint', () => {
    test('GET /api/stats returns correct structure', async ({ request }) => {
      const response = await request.get(`${API_BASE}/api/stats`);
      expect(response.ok()).toBeTruthy();
      
      const data: Stats = await response.json();
      
      // Validate all required fields
      expect(data).toHaveProperty('pipelines_count');
      expect(data).toHaveProperty('subscriptions_count');
      expect(data).toHaveProperty('total_runs');
      
      // Validate types
      expect(typeof data.pipelines_count).toBe('number');
      expect(typeof data.subscriptions_count).toBe('number');
      expect(typeof data.total_runs).toBe('number');
    });
  });

  test.describe('Edge Cases', () => {
    test('handles empty arrays correctly', async ({ request }) => {
      // Even with no data, endpoints should return empty arrays, not null
      const endpoints = [
        '/api/subscriptions',
        '/api/subscriptions/stats',
        '/api/pipelines',
        '/api/runs',
      ];
      
      for (const endpoint of endpoints) {
        const response = await request.get(`${API_BASE}${endpoint}`);
        expect(response.ok()).toBeTruthy();
        
        const data = await response.json();
        expect(Array.isArray(data)).toBeTruthy();
      }
    });

    test('API returns JSON for valid endpoints', async ({ request }) => {
      // Verify that API endpoints return JSON, not HTML
      const response = await request.get(`${API_BASE}/api/health`);
      const contentType = response.headers()['content-type'];
      expect(contentType).toContain('application/json');
    });
  });
});
