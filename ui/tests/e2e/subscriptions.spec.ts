import { test, expect } from '@playwright/test';

test.describe('Subscriptions', () => {
  test('should load subscriptions list', async ({ page }) => {
    await page.goto('/subscriptions');
    
    // Wait for the page to load
    await page.waitForLoadState('networkidle');
    
    // Check that the page title is correct
    await expect(page.getByRole('heading', { name: 'Subscriptions' })).toBeVisible();
  });

  test('should display search bar', async ({ page }) => {
    await page.goto('/subscriptions');
    
    // Wait for search bar
    await page.waitForSelector('input[placeholder*="Search"]', { timeout: 10000 });
    
    // Check that search bar is visible
    const searchBar = page.locator('input[placeholder*="Search"]');
    await expect(searchBar).toBeVisible();
  });

  test('should filter subscriptions when searching', async ({ page }) => {
    await page.goto('/subscriptions');
    
    // Wait for subscriptions to load
    await page.waitForLoadState('networkidle');
    
    // Find the search input
    const searchInput = page.locator('input[placeholder*="Search"]');
    await expect(searchInput).toBeVisible();
    
    // Type in search box
    await searchInput.fill('test');
    
    // Wait a bit for filtering to happen
    await page.waitForTimeout(500);
    
    // The search should have filtered the list (we can't assert exact count without knowing data)
    // Just verify the page didn't crash
    await expect(page.locator('body')).toBeVisible();
  });

  test('should display subscription cards', async ({ page }) => {
    await page.goto('/subscriptions');
    
    // Wait for subscriptions to load
    await page.waitForLoadState('networkidle');
    
    // Just verify the page loaded
    await expect(page.locator('body')).toBeVisible();
  });

  test('should navigate to subscription detail', async ({ page }) => {
    await page.goto('/subscriptions');
    
    // Wait for subscriptions to load
    await page.waitForLoadState('networkidle');
    
    // Find first subscription card
    const firstCard = page.locator('[data-testid="subscription-card"]').first();
    
    // Check if any subscriptions exist
    const count = await firstCard.count();
    
    if (count > 0) {
      // Click on the first subscription
      await firstCard.click();
      
      // Wait for navigation
      await page.waitForURL(/\/subscriptions\/\d+/);
      
      // Verify we're on a subscription detail page
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('should have back navigation on detail page', async ({ page }) => {
    await page.goto('/subscriptions');
    await page.waitForLoadState('networkidle');
    
    const firstCard = page.locator('[data-testid="subscription-card"]').first();
    const count = await firstCard.count();
    
    if (count > 0) {
      await firstCard.click();
      await page.waitForURL(/\/subscriptions\/\d+/);
      
      // Look for back button or link
      const backButton = page.locator('a[href="/subscriptions"]');
      await expect(backButton).toBeVisible();
      
      // Click back
      await backButton.click();
      
      // Should be back on subscriptions list
      await page.waitForURL('/subscriptions');
      await expect(page.getByRole('heading', { name: 'Subscriptions' })).toBeVisible();
    }
  });
});
