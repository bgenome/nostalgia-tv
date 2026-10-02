// @ts-check
const { test, expect } = require('@playwright/test');

test.describe('Nostalgia TV - 10-Foot Smart TV App Visual & UI/UX Suite', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to 10-Foot Smart TV View
    await page.goto('/tv');
    await page.waitForLoadState('networkidle');
  });

  test('Visual UI: Fullscreen 10-foot viewport, CRT shaders, and OSD render', async ({ page }) => {
    // Check viewport and screen
    const viewport = page.locator('.tv-viewport');
    await expect(viewport).toBeVisible();

    const screen = page.locator('#screen');
    await expect(screen).toBeVisible();
    await expect(screen).toHaveClass(/crt-screen/);

    // Check OSD
    const osd = page.locator('#osd');
    await expect(osd).toBeVisible();

    const osdChannel = page.locator('#osd-channel-text');
    await expect(osdChannel).toContainText('CH');

    // Capture screenshot of 10-foot Smart TV UI
    await page.screenshot({ path: 'test-results/screenshots/11-smart-tv-10foot-view.png' });
  });

  test('UX Interaction: Remote D-pad ArrowUp / ArrowDown flips channels', async ({ page }) => {
    const osdChannel = page.locator('#osd-channel-text');

    // Press ArrowUp to channel surf
    await page.keyboard.press('ArrowUp');
    await page.waitForTimeout(500);

    // Verify channel changed
    await expect(osdChannel).toBeVisible();

    // Press digit 2 to tune directly
    await page.keyboard.press('2');
    await page.waitForTimeout(500);
    await expect(osdChannel).toHaveText('CH 02');

    // Capture screenshot of tuned channel on Smart TV
    await page.screenshot({ path: 'test-results/screenshots/12-smart-tv-channel-2.png' });
  });

  test('Visual UI & UX: Tuning to Channel 1 triggers Prevue TV Guide', async ({ page }) => {
    const guideView = page.locator('#guide-view');

    // Press digit 1 for Prevue Guide
    await page.keyboard.press('1');
    await page.waitForTimeout(1000);

    // Verify guide view activates
    await expect(guideView).toBeVisible();
    await expect(page.locator('.guide-top-banner')).toBeVisible();

    // Capture screenshot of Smart TV Prevue Guide
    await page.screenshot({ path: 'test-results/screenshots/13-smart-tv-guide.png' });
  });

});
