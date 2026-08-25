// Renders slide HTML files (slides/slide-*.html) to 1080x1080 PNGs (slides/slide-*.png)
// Usage: node render_slides.js <dir-with-html-files>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const dir = process.argv[2] || path.join(__dirname, '..', 'slides');
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.html')).sort();
  if (files.length === 0) {
    console.error('No HTML files found in', dir);
    process.exit(1);
  }
  // PLAYWRIGHT_CHROMIUM_PATH lets a specific sandbox pin an exact Chromium binary;
  // when unset (e.g. in GitHub Actions after `npx playwright install chromium`),
  // Playwright resolves its own bundled Chromium automatically.
  const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || undefined, args: ['--force-color-profile=srgb']});
  const page = await browser.newPage({ viewport: { width: 1080, height: 1080 }, deviceScaleFactor: 1 });
  for (const f of files) {
    const filePath = path.resolve(dir, f);
    await page.goto('file://' + filePath);
    await page.waitForTimeout(150);
    const outPath = filePath.replace(/\.html$/, '.png');
    await page.screenshot({ path: outPath, clip: { x: 0, y: 0, width: 1080, height: 1080 } });
    console.log('Rendered', outPath);
  }
  await browser.close();
})();
