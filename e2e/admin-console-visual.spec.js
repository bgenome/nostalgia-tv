// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Nostalgia TV - Station Control Room Visual & UI/UX Suite', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to Admin Console
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
  });

  test('Visual UI: Station Control Room header, navigation, and live monitor render', async ({ page }) => {
    // Check Brand and Header
    const badge = page.locator('.brand-badge');
    await expect(badge).toHaveText('NOSTALGIA TV');

    const brand = page.locator('.brand-title');
    await expect(brand).toContainText('Control Station & Media Scheduler');

    // Check Navigation Buttons in Sidebar
    const navButtons = page.locator('.sidebar .nav-btn');
    await expect(navButtons).toHaveCount(5);
    await expect(navButtons.nth(0)).toContainText('Live TV & Remote');
    await expect(navButtons.nth(1)).toContainText('Channel Manager');
    await expect(navButtons.nth(2)).toContainText('Plex Media Server');
    await expect(navButtons.nth(3)).toContainText('YouTube Channels');
    await expect(navButtons.nth(4)).toContainText('Station & Shaders');

    // Check Live TV Monitor
    const monitorVideo = page.locator('#monitor-video');
    await expect(monitorVideo).toBeVisible();
    await expect(page.locator('#preview-osd')).toBeVisible();

    // Check Quick Remote in Monitor tab
    await expect(page.getByRole('button', { name: /Power/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Trigger Commercial Break/i })).toBeVisible();

    // Capture screenshot of Admin Dashboard
    await page.screenshot({ path: 'test-results/screenshots/06-admin-dashboard.png', fullPage: true });
  });

  test('UX Interaction: Channel Manager tab lists active channels', async ({ page }) => {
    // Switch to Channel Manager Tab
    await page.locator('.sidebar .nav-btn', { hasText: 'Channel Manager' }).click();

    // Verify Channel cards list is displayed
    const list = page.locator('#channel-cards-list');
    await expect(list).toBeVisible();

    // Verify channel cards populate
    await page.waitForTimeout(600);
    await expect(list).toContainText('TV GUIDE (PREVUE)');
    await expect(list).toContainText('SUPERMAN 1941');

    // Capture Channels list screenshot
    await page.screenshot({ path: 'test-results/screenshots/07-admin-channels-tab.png' });
  });

  test('UX Interaction: Plex Media Server tab displays configuration and libraries', async ({ page }) => {
    // Switch to Plex Tab
    await page.locator('.sidebar .nav-btn', { hasText: 'Plex Media Server' }).click();

    // Check connection status badge
    const badge = page.locator('#plex-status-badge');
    await expect(badge).toBeVisible();

    // Wait for connection test to populate info
    await page.waitForTimeout(1000);
    const info = page.locator('#plex-server-info');
    await expect(info).toBeVisible();

    // Verify library cards or container exists
    const libsContainer = page.locator('#plex-libs-container');
    await expect(libsContainer).toBeVisible();

    // Capture Plex Explorer screenshot
    await page.screenshot({ path: 'test-results/screenshots/08-admin-plex-explorer.png' });
  });

  test('UX Interaction: YouTube Channels tab displays curated channel quick-chips', async ({ page }) => {
    // Switch to YouTube Tab
    await page.locator('.sidebar .nav-btn', { hasText: 'YouTube Channels' }).click();

    // Verify curated channel chips exist
    await expect(page.getByRole('button', { name: /Super Simple Songs/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Ms Rachel/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Sesame Street/i })).toBeVisible();

    // Click Super Simple Songs chip and verify URL field fills
    await page.getByRole('button', { name: /Super Simple Songs/i }).click();
    const urlInput = page.locator('#yt-url-input');
    await expect(urlInput).toHaveValue('https://www.youtube.com/@SuperSimpleSongs');

    // Capture YouTube tab screenshot
    await page.screenshot({ path: 'test-results/screenshots/09-admin-youtube-tab.png' });
  });

  test('UX Interaction: Station & Shaders tab displays CRT aesthetic preferences', async ({ page }) => {
    // Switch to Settings Tab
    await page.locator('.sidebar .nav-btn', { hasText: 'Station & Shaders' }).click();

    // Check Station Settings Card
    const stationNameInput = page.locator('#station-name-input');
    await expect(stationNameInput).toBeVisible();
    await expect(stationNameInput).toHaveValue(/NOSTALGIA TV/);

    // Verify CRT Scanlines toggle & boot video select
    await expect(page.locator('#scanlines-toggle')).toBeVisible();
    await expect(page.locator('#boot-video-select')).toBeVisible();

    // Capture Settings tab screenshot
    await page.screenshot({ path: 'test-results/screenshots/10-admin-settings-tab.png' });
  });

});
