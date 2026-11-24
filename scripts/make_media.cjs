// Regenerates docs/media/* from the invented demo dish. Nothing from your machine is used.
//   agent-dish demo --end 2026-11-20 --out /tmp/sc-demo
//   npm i playwright   (or point NODE_PATH at an install)  &&  node scripts/make_media.cjs /tmp/sc-demo/agent-dish-demo.html docs/media
// Needs ffmpeg for the GIF. Set SC_CHANNEL=chrome (default) or SC_CHANNEL= to use Playwright's own Chromium.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');

const [html, out] = [process.argv[2], process.argv[3] || 'docs/media'];
const url = 'file://' + path.resolve(html) + '?seed=' + (process.env.SC_SEED || 40);
const FRAMES = 72, SIZE = { width: 1280, height: 800 };
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch(process.env.SC_CHANNEL === '' ? {} : { channel: process.env.SC_CHANNEL || 'chrome' });
  const open = async (legend) => {   // a fresh page: legend visible or hidden, paused at a fraction of the replay
    const ctx = await browser.newContext({ viewport: SIZE });
    const page = await ctx.newPage();
    await page.addInitScript(l => localStorage.setItem('agent-dish-legend', l), legend ? '1' : '0');
    await page.goto(url); await sleep(1200);
    return page;
  };
  const at = async (page, f, wait = 2600) => { await page.fill('#scrub', String(Math.round(f * 1000))); await page.dispatchEvent('#scrub', 'input'); await sleep(wait); };

  let page = await open(false);
  await at(page, 0.74, 4200);
  await page.screenshot({ path: path.join(out, 'dish.png') });

  // click the biggest session that others built on
  const spot = await page.evaluate(() => {
    const r = document.getElementById('dish').getBoundingClientRect();
    const c = dn.filter(p => p.d.start <= now && p.d.kids > 0).sort((a, b) => radiusAt(b.d) - radiusAt(a.d))[0];
    return c && { x: r.left + DW/2 + c.x, y: r.top + DH/2 - 28 + c.y };
  });
  if (spot) { await page.mouse.click(spot.x, spot.y); await sleep(600); await page.screenshot({ path: path.join(out, 'card.png') }); }
  await page.context().close();

  page = await open(true);
  await at(page, 0.74, 4200);
  await page.screenshot({ path: path.join(out, 'legend.png') });
  await page.context().close();

  // the GIF: step the dish clock through the replay, letting the physics settle a little between frames
  page = await open(false);
  const frames = fs.mkdtempSync(path.join(require('os').tmpdir(), 'sc-frames-'));
  for (let i = 0; i < FRAMES; i++) {
    await at(page, 0.04 + 0.94 * i / (FRAMES - 1), i === 0 ? 2500 : 220);
    await page.screenshot({ path: path.join(frames, String(i).padStart(3, '0') + '.png') });
  }
  await browser.close();
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '8', '-i', path.join(frames, '%03d.png'), '-vf',
    'scale=840:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=160:stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a',
    '-loop', '0', path.join(out, 'dish.gif')]);
  console.log('wrote', fs.readdirSync(out).join(', '));
})();
