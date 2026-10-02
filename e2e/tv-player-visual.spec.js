// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Nostalgia TV - Web TV Visual & UI/UX Suite', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to TV View
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Visual UI: Trinitron CRT Bezel, Power LED, and Virtual Remote render correctly', async ({ page }) => {
    // Check main TV frame and bezel
    const tvFrame = page.locator('.tv-frame');
    await expect(tvFrame).toBeVisible();

    const tvBezel = page.locator('.tv-bezel');
    await expect(tvBezel).toBeVisible();

    // Check CRT screen
    const screen = page.locator('#screen');
    await expect(screen).toBeVisible();
    await expect(screen).toHaveClass(/crt-screen/);

    // Check Trinitron branding
    const brand = page.locator('.tv-brand');
    await expect(brand).toContainText('TRINITRON NOSTALGIA CRT');

    // Check Power LED exists and is visible
    const powerLed = page.locator('#power-led');
    await expect(powerLed).toBeVisible();

    // Check LG Magic Virtual Remote is visible
    const remote = page.locator('.lg-remote');
    await expect(remote).toBeVisible();
    await expect(remote.locator('.remote-brand')).toHaveText('LG MAGIC');

    // Take screenshot of default TV UI
    await page.screenshot({ path: 'test-results/screenshots/01-tv-default-ui.png', fullPage: true });
  });

  test('UX Interaction: CRT Filter and Scanline toggles modify styling correctly', async ({ page }) => {
    const screen = page.locator('#screen');
    const scanlines = page.locator('#scanlines-layer');
    const crtBtn = page.getByRole('button', { name: 'CRT Filter' });
    const scanlinesBtn = page.getByRole('button', { name: 'Scanlines' });

    // Initially curvature is ON
    await expect(screen).toHaveClass(/curvature-on/);

    // Toggle CRT Filter OFF (flat screen)
    await crtBtn.click();
    await expect(screen).not.toHaveClass(/curvature-on/);
    await page.screenshot({ path: 'test-results/screenshots/02-tv-flat-screen.png' });

    // Toggle CRT Filter back ON (curved Trinitron tube)
    await crtBtn.click();
    await expect(screen).toHaveClass(/curvature-on/);

    // Toggle scanlines
    await scanlinesBtn.click();
    await expect(scanlines).toHaveCSS('display', 'none');

    await scanlinesBtn.click();
    await expect(scanlines).toHaveCSS('display', 'block');
  });

  test('UX Interaction: Surfing channels updates OSD and triggers static noise burst', async ({ page }) => {
    const osd = page.locator('#osd');
    const osdChannel = page.locator('#osd-channel-text');
    const osdTitle = page.locator('#osd-title-text');
    const staticCanvas = page.locator('#static-canvas');

    // Initial state (CH 2 or current)
    await expect(osd).toBeVisible();
    await expect(osdChannel).toContainText('CH');

    // Click Channel 3 on remote keypad
    const key3 = page.locator('.num-btn', { hasText: '3' });
    await key3.click();

    // Verify OSD updates to CH 03
    await expect(osdChannel).toHaveText('CH 03');
    await expect(osdTitle).toBeVisible();

    // Verify static canvas is present in DOM
    await expect(staticCanvas).toBeAttached();

    // Capture screenshot of tuned channel
    await page.screenshot({ path: 'test-results/screenshots/03-channel-3-tuned.png' });

    // Test CH Up rocker button
    const chCol = page.locator('.rocker-col', { hasText: 'CH' });
    const chUpBtn = chCol.locator('.rocker-btn').first();
    await chUpBtn.click();
    await expect(osdChannel).toHaveText('CH 04');
  });

  test('Visual UI & UX: Prevue TV Guide Channel 1 renders schedule grid & clock', async ({ page }) => {
    const guideView = page.locator('#guide-view');
    const guideClock = page.locator('#guide-clock');

    // Tune directly to Channel 1 using remote button '1'
    const key1 = page.locator('.num-btn', { hasText: '1' });
    await key1.click();

    // Wait for Guide View to become visible
    await expect(guideView).toBeVisible({ timeout: 7000 });

    // Check Prevue header and live clock
    const banner = page.locator('.guide-top-banner');
    await expect(banner).toContainText('NOSTALGIA TV PREVUE');
    await expect(guideClock).toBeVisible();

    // Wait for the schedule grid rows to populate
    await page.waitForTimeout(1000);
    const gridRows = page.locator('.guide-row');
    const count = await gridRows.count();
    expect(count).toBeGreaterThanOrEqual(1);

    // Capture screenshot of Prevue TV Guide
    await page.screenshot({ path: 'test-results/screenshots/04-prevue-guide-matrix.png' });
  });

  test('UX Interaction: Power button toggles TV standby mode', async ({ page }) => {
    const powerBtn = page.locator('.btn-power');
    const screen = page.locator('#screen');

    // Click power to turn OFF (screen brightness set to 0)
    await powerBtn.click();
    await expect(screen).toHaveCSS('filter', 'brightness(0)');

    // Capture TV OFF screenshot
    await page.screenshot({ path: 'test-results/screenshots/05-tv-powered-off.png' });

    // Click power to turn back ON (filter restored to none)
    await powerBtn.click();
    await expect(screen).toHaveCSS('filter', 'none');
  });

});
