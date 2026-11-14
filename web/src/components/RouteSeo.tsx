import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { getPageMetadata, SITE_URL, structuredData } from '@/lib/seo';

// Update existing head elements so client-side navigation never retains About metadata.
export function RouteSeo() {
  const { pathname } = useLocation();
  useEffect(() => {
    const page = getPageMetadata(pathname);
    document.title = page.title;
    const meta = (attribute: 'name' | 'property', key: string, content: string) => {
      let element = document.head.querySelector<HTMLMetaElement>(`meta[${attribute}="${key}"]`);
      if (!element) {
        element = document.createElement('meta');
        element.setAttribute(attribute, key);
        document.head.appendChild(element);
      }
      element.content = content;
    };
    meta('name', 'description', page.description);
    meta('name', 'robots', page.noindex ? 'noindex, follow' : 'index, follow');
    meta('property', 'og:type', 'website');
    meta('property', 'og:site_name', 'Liquorfy');
    meta('property', 'og:title', page.title);
    meta('property', 'og:description', page.description);
    meta('property', 'og:url', page.canonical);
    meta('property', 'og:image', `${SITE_URL}/branding/og-image.png`);
    meta('name', 'twitter:card', 'summary_large_image');
    meta('name', 'twitter:title', page.title);
    meta('name', 'twitter:description', page.description);
    meta('name', 'twitter:image', `${SITE_URL}/branding/og-image.png`);
    let canonical = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.rel = 'canonical';
      document.head.appendChild(canonical);
    }
    canonical.href = page.canonical;
    const data = structuredData(pathname);
    let schema = document.getElementById('page-structured-data');
    if (data) {
      if (!schema) {
        schema = document.createElement('script');
        schema.id = 'page-structured-data';
        schema.setAttribute('type', 'application/ld+json');
        document.head.appendChild(schema);
      }
      schema.textContent = JSON.stringify(data).replace(/</g, '\\u003c');
    } else {
      schema?.remove();
    }
  }, [pathname]);
  return null;
}
