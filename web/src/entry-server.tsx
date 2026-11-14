import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom';
import About from './pages/About';
import Privacy from './pages/Privacy';
import Support from './pages/Support';
import Terms from './pages/Terms';
import { getPageMetadata, publicPages, SITE_URL, staticPaths, structuredData } from './lib/seo';

export { publicPages, SITE_URL, staticPaths };

const escape = (value: string) => value.replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[char]!);

export function render(path: string) {
  const page = getPageMetadata(path);
  const components = { '/about': About, '/privacy': Privacy, '/support': Support, '/terms': Terms };
  const Component = components[path as keyof typeof components];
  const schema = structuredData(path);
  const head = [
    `<title>${escape(page.title)}</title>`,
    `<meta name="description" content="${escape(page.description)}" />`,
    '<meta name="robots" content="index, follow" />',
    `<link rel="canonical" href="${page.canonical}" />`,
    '<meta property="og:type" content="website" />',
    '<meta property="og:site_name" content="Liquorfy" />',
    '<meta property="og:locale" content="en_NZ" />',
    `<meta property="og:title" content="${escape(page.title)}" />`,
    `<meta property="og:description" content="${escape(page.description)}" />`,
    `<meta property="og:url" content="${page.canonical}" />`,
    `<meta property="og:image" content="${SITE_URL}/branding/og-image.png" />`,
    '<meta name="twitter:card" content="summary_large_image" />',
    `<meta name="twitter:title" content="${escape(page.title)}" />`,
    `<meta name="twitter:description" content="${escape(page.description)}" />`,
    `<meta name="twitter:image" content="${SITE_URL}/branding/og-image.png" />`,
    ...(schema ? [`<script id="page-structured-data" type="application/ld+json">${JSON.stringify(schema).replace(/</g, '\\u003c')}</script>`] : []),
  ].join('\n    ');
  return { head, html: Component ? renderToString(<StaticRouter location={path}><Component /></StaticRouter>) : '' };
}
