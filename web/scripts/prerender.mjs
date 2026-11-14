import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { createServer } from 'vite';

const server = await createServer({
  server: { middlewareMode: true, hmr: false, ws: false, watch: null },
  // React Router 7 publishes its Node ESM entry under module-sync; Vite 5's SSR
  // loader otherwise selects its CommonJS entry and misses re-exported names.
  ssr: { resolve: { externalConditions: ['module-sync'] } },
  appType: 'custom',
  optimizeDeps: { noDiscovery: true },
});
try {
  const { render, publicPages, SITE_URL, staticPaths } = await server.ssrLoadModule('/src/entry-server.tsx');
  const template = await readFile('dist/index.html', 'utf8');
  if (!template.includes('<!--seo:start-->') || !template.includes('<div id="root"></div>')) {
    throw new Error('Prerender template markers are missing');
  }
  for (const path of ['/', ...staticPaths]) {
    const { head, html } = render(path);
    const filename = path === '/' ? 'dist/index.html' : `dist${path}.html`;
    await mkdir(dirname(filename), { recursive: true });
    await writeFile(filename, template
      .replace(/<!--seo:start-->[\s\S]*?<!--seo:end-->/, () => `<!--seo:start-->\n    ${head}\n    <!--seo:end-->`)
      .replace('<div id="root"></div>', () => `<div id="root">${html}</div>`));
  }
  // Dynamic products remain out of this static sitemap: no guessed IDs or API dependency.
  await writeFile('dist/sitemap.xml', `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${Object.keys(publicPages).map(path => `  <url><loc>${SITE_URL}${path}</loc></url>`).join('\n')}\n</urlset>\n`);
  console.log(`Prerendered ${staticPaths.length} public information pages and homepage metadata.`);
} finally {
  await server.close();
}
