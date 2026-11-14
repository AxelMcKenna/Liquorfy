// Match the existing production Open Graph hostname throughout this change.
export const SITE_URL = 'https://www.liquorfy.co.nz';
const personId = 'https://damascus-llm.dev/axel-mckenna#person';

export const publicPages: Record<string, { title: string; description: string }> = {
  '/': {
    title: 'Liquorfy - Compare Liquor Prices in New Zealand',
    description: 'Find the best liquor prices across New Zealand retailers. Compare beer, wine, and spirits from stores near you.',
  },
  '/about': {
    title: 'About Liquorfy - Created by Axel McKenna',
    description: 'Meet Liquorfy, the New Zealand liquor price comparison platform created by Axel McKenna. Compare beer, wine, spirits, pack sizes, and offers in one place.',
  },
  '/explore': {
    title: 'Compare Beer, Wine and Spirits Prices - Liquorfy',
    description: 'Explore liquor prices from New Zealand retailers. Filter beer, wine, and spirits and compare prices at stores near you.',
  },
  '/privacy': { title: 'Privacy Policy - Liquorfy', description: 'How Liquorfy handles your data, location preferences, account information, and privacy.' },
  '/support': { title: 'Support - Liquorfy', description: 'Get help with Liquorfy, report a pricing issue, or contact the team with feedback.' },
  '/terms': { title: 'Terms of Service - Liquorfy', description: 'Read the terms for using Liquorfy, New Zealand’s liquor price comparison service.' },
};

export const staticPaths = ['/about', '/privacy', '/support', '/terms'];

export function getPageMetadata(pathname: string) {
  const path = pathname.replace(/\/$/, '') || '/';
  const page = publicPages[path];
  const product = /^\/product\/[^/]+$/.test(path);
  return {
    ...(page ?? (product ? publicPages['/'] : {
      title: 'Liquorfy', description: 'New Zealand liquor price comparison.',
    })),
    canonical: `${SITE_URL}${path}`,
    noindex: !page && !product,
  };
}

export function structuredData(pathname: string) {
  const path = pathname.replace(/\/$/, '') || '/';
  if (path !== '/' && path !== '/about') return null;
  const person = {
    '@type': 'Person', '@id': personId, name: 'Axel McKenna',
    url: 'https://damascus-llm.dev/axel-mckenna', sameAs: ['https://github.com/AxelMcKenna'],
  };
  const website = {
    '@type': 'WebSite', '@id': `${SITE_URL}/#website`, url: `${SITE_URL}/`, name: 'Liquorfy',
    description: publicPages['/'].description, creator: { '@id': personId }, inLanguage: 'en-NZ',
  };
  return {
    '@context': 'https://schema.org', '@graph': [person, website, ...(path === '/about' ? [{
      '@type': 'AboutPage', '@id': `${SITE_URL}/about`, url: `${SITE_URL}/about`,
      name: publicPages['/about'].title, about: [{ '@id': `${SITE_URL}/#website` }, { '@id': personId }],
      isPartOf: { '@id': `${SITE_URL}/#website` },
    }] : [])],
  };
}
