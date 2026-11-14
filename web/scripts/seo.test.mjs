import assert from 'node:assert/strict';
import { access, readFile } from 'node:fs/promises';
import { after, before, test } from 'node:test';
import { createServer, preview } from 'vite';

const origin = 'https://www.liquorfy.co.nz';
const paths = ['/about', '/privacy', '/support', '/terms'];
const schemas = html => [...html.matchAll(/<script[^>]+type="application\/ld\+json"[^>]*>([\s\S]*?)<\/script>/g)].map(match => JSON.parse(match[1]));
let server;
let seo;
before(async () => {
  server = await createServer({ server: { middlewareMode: true, hmr: false, ws: false, watch: null }, appType: 'custom', optimizeDeps: { noDiscovery: true } });
  seo = await server.ssrLoadModule('/src/lib/seo.ts');
});
after(async () => { await server?.close(); });

for (const path of ['/', ...paths]) {
  test(`${path} has one canonical, matching metadata, and valid assets`, async () => {
    const html = await readFile(path === '/' ? 'dist/index.html' : `dist${path}.html`, 'utf8');
    assert.equal((html.match(/<title>/g) ?? []).length, 1);
    assert.equal((html.match(/rel="canonical"/g) ?? []).length, 1);
    assert.ok(html.includes(`rel="canonical" href="${origin}${path}"`));
    assert.ok(html.includes(`property="og:url" content="${origin}${path}"`));
    assert.match(html, /name="twitter:card" content="summary_large_image"/);
    assert.doesNotMatch(html, /noindex|localhost|127\.0\.0\.1/);
    if (path !== '/') {
      assert.equal((html.match(/<h1\b/g) ?? []).length, 1);
      assert.match(html, /href="\/about"/);
      assert.match(html, /Created by/);
    }
    for (const match of html.matchAll(/(?:src|href)="(\/assets\/[^"?#]+)"/g)) await access(`dist${match[1]}`);
  });
}

test('About has real HTML attribution and consistent creator structured data', async () => {
  const html = await readFile('dist/about.html', 'utf8');
  assert.match(html, /Built by Axel McKenna/);
  assert.match(html, /href="https:\/\/damascus-llm\.dev\/axel-mckenna"/);
  const graph = schemas(html)[0]['@graph'];
  const person = graph.find(node => node['@type'] === 'Person');
  assert.equal(person['@id'], 'https://damascus-llm.dev/axel-mckenna#person');
  assert.equal(graph.find(node => node['@type'] === 'WebSite').creator['@id'], person['@id']);
  assert.ok(graph.find(node => node['@type'] === 'AboutPage'));
});

test('public/product routes retain indexing and their own canonicals; private/error routes do not index', () => {
  for (const path of ['/', '/about', '/about/', '/explore', '/product/example-id']) {
    assert.equal(seo.getPageMetadata(path).noindex, false);
  }
  assert.equal(seo.getPageMetadata('/product/example-id').canonical, `${origin}/product/example-id`);
  assert.equal(seo.getPageMetadata('/about/').canonical, `${origin}/about`);
  for (const path of ['/login', '/register', '/auth/callback', '/settings', '/watchlist', '/reset-password', '/forgot-password', '/missing']) {
    assert.equal(seo.getPageMetadata(path).noindex, true);
    assert.equal(seo.structuredData(path), null);
  }
  assert.equal(seo.structuredData('/product/example-id'), null);
  assert.equal(seo.getPageMetadata('/explore').title, 'Compare Beer, Wine and Spirits Prices - Liquorfy');
});

test('static information pages bypass the SPA fallback in Vercel', async () => {
  const config = JSON.parse(await readFile('vercel.json', 'utf8'));
  for (const path of paths) {
    const rule = config.rewrites.find(rule => rule.source === path);
    assert.equal(rule?.destination, `${path}.html`);
    assert.ok(config.rewrites.indexOf(rule) < config.rewrites.findIndex(rule => rule.source === '/(.*)'));
    await access(`dist${rule.destination}`);
  }
});

test('robots and sitemap list public pages without guessed product or private URLs', async () => {
  const robots = await readFile('dist/robots.txt', 'utf8');
  const sitemap = await readFile('dist/sitemap.xml', 'utf8');
  assert.ok(robots.includes(`Sitemap: ${origin}/sitemap.xml`));
  assert.deepEqual([...sitemap.matchAll(/<loc>(.*?)<\/loc>/g)].map(match => match[1]), Object.keys(seo.publicPages).map(path => `${origin}${path}`));
  assert.doesNotMatch(sitemap, /\/product\/|\/settings|\/login|\/watchlist/);
});

test('extensionless information pages serve their own HTML; app routes keep the SPA fallback', async () => {
  const previewServer = await preview({ preview: { host: '127.0.0.1', port: 0, open: false } });
  try {
    const address = previewServer.httpServer.address();
    for (const path of paths) {
      const response = await fetch(`http://127.0.0.1:${address.port}${path}`);
      assert.equal(response.status, 200);
      assert.equal(await response.text(), await readFile(`dist${path}.html`, 'utf8'));
    }
    for (const path of ['/explore?q=beer', '/product/example-id', '/login', '/auth/callback']) {
      const response = await fetch(`http://127.0.0.1:${address.port}${path}`);
      assert.equal(response.status, 200);
      assert.equal(await response.text(), await readFile('dist/index.html', 'utf8'));
    }
    for (const path of ['/robots.txt', '/sitemap.xml', '/llms.txt']) {
      const response = await fetch(`http://127.0.0.1:${address.port}${path}`);
      assert.equal(response.status, 200);
      assert.equal(await response.text(), await readFile(`dist${path}`, 'utf8'));
    }
  } finally {
    await new Promise((resolve, reject) => previewServer.httpServer.close(error => error ? reject(error) : resolve()));
  }
});

test('AI discovery summary identifies the creator without publishing invented live prices', async () => {
  const summary = await readFile('dist/llms.txt', 'utf8');
  assert.match(summary, /^# Liquorfy/);
  assert.match(summary, /created by Axel McKenna/);
  assert.match(summary, /does not contain live product prices/);
  assert.match(summary, /inference optimisation/);
  assert.doesNotMatch(summary, /\/settings|\/watchlist|\/auth\//);
  const robots = await readFile('dist/robots.txt', 'utf8');
  for (const agent of ['OAI-SearchBot', 'Claude-SearchBot']) assert.ok(robots.includes(`User-agent: ${agent}\nAllow: /`));
  assert.match(await readFile('dist/about.html', 'utf8'), /rel="describedby" href="\/llms.txt"/);
});
