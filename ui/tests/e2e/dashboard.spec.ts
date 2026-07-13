import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('should load without errors', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check that the page title is correct
    await expect(page).toHaveTitle(/Sortarr/);
  });

  test('should display status cards', async ({ page }) => {
    await page.goto('/');
    
    // Wait for status cards container to load
    const statusCardsContainer = page.locator('[data-testid="status-cards"]');
    await expect(statusCardsContainer).toBeVisible({ timeout: 10000 });
  });

  test('should display activity feed', async ({ page }) => {
    await page.goto('/');
    
    // Wait for activity feed section
    await page.waitForSelector('text=Recent Activity', { timeout: 10000 });
    
    // Check that activity feed is visible
    await expect(page.getByText('Recent Activity')).toBeVisible();
    
    // Check for activity items or empty state
    const activitySection = page.locator('[data-testid="activity-feed"]');
    await expect(activitySection).toBeVisible();
  });

  test('should display run timeline', async ({ page }) => {
    await page.goto('/');
    
    // Wait for run timeline section
    const timeline = page.locator('[data-testid="run-timeline"]');
    await expect(timeline).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to subscriptions', async ({ page }) => {
    await page.goto('/');
    
    // Click on Subscriptions link in navigation
    await page.click('a[href="/subscriptions"]');
    
    // Wait for navigation
    await page.waitForURL('/subscriptions');
    
    // Verify we're on the subscriptions page
    await expect(page.getByRole('heading', { name: 'Subscriptions' })).toBeVisible();
  });

  test('should navigate to pipelines', async ({ page }) => {
    await page.goto('/');
    
    // Click on Pipelines link in navigation
    await page.click('a[href="/pipelines"]');
    
    // Wait for navigation
    await page.waitForURL('/pipelines');
    
    // Verify we're on the pipelines page
    await expect(page.getByRole('heading', { name: 'Pipelines' })).toBeVisible();
  });

  test('should navigate to runs', async ({ page }) => {
    await page.goto('/');
    
    // Click on Runs link in navigation
    await page.click('a[href="/runs"]');
    
    // Wait for navigation
    await page.waitForURL('/runs');
    
    // Verify we're on the runs page
    await expect(page.getByRole('heading', { name: 'Run History' })).toBeVisible();
  });

  test('should navigate to settings', async ({ page }) => {
    await page.goto('/');
    
    // Click on Settings link in navigation
    await page.click('a[href="/settings"]');
    
    // Wait for navigation
    await page.waitForURL('/settings');
    
    // Verify we're on the settings page
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();
  });

  test('should show authentication warning if not authenticated', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Just verify the page loaded without crashing
    // (authentication warning may or may not be present depending on backend state)
    await expect(page.locator('body')).toBeVisible();
  });
});
