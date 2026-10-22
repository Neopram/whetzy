/**
 * Datos estructurados de la landing (schema.org, JSON-LD), ola 2 2026-10-21.
 * Solo lo que el producto hace hoy y los precios de `plans.ts`, que
 * `backend/tests/test_constantes_planes.py` ata a `app/core/prices.py`. Sin
 * valoraciones ni número de usuarios: no hay datos reales que darlos (30.1).
 * El plan Creador no sale: su precio no se publica en la landing (D-7).
 */
import { CATALOG_TRACKS } from './catalog';
import { PRO_MAX_MONTHLY_USD, PRO_MONTHLY_USD } from './plans';

export const SITE_URL = 'https://whetzy.com';

type Lang = 'es' | 'en';

const TEXT = {
  es: {
    description: `Práctica adaptativa para certificaciones y programación, en español e inglés: ${CATALOG_TRACKS} rutas, repaso espaciado y preparación por dominio del examen.`,
    free: 'Gratis',
    pro: 'Pro (mensual)',
    proMax: 'Pro Max (mensual)',
  },
  en: {
    description: `Adaptive practice for certifications and programming, in English and Spanish: ${CATALOG_TRACKS} tracks, spaced repetition and readiness by exam domain.`,
    free: 'Free',
    pro: 'Pro (monthly)',
    proMax: 'Pro Max (monthly)',
  },
} as const;

function offer(name: string, price: number) {
  return { '@type': 'Offer', name, price: price.toFixed(2), priceCurrency: 'USD', url: `${SITE_URL}/landing#pricing` };
}

export function landingJsonLd(lang: Lang): Record<string, unknown> {
  const t = TEXT[lang];
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Organization',
        '@id': `${SITE_URL}/#org`,
        name: 'Whetzy',
        url: SITE_URL,
        logo: `${SITE_URL}/favicon.svg`,
      },
      {
        '@type': 'WebSite',
        '@id': `${SITE_URL}/#website`,
        name: 'Whetzy',
        url: SITE_URL,
        inLanguage: ['es', 'en'],
        publisher: { '@id': `${SITE_URL}/#org` },
      },
      {
        '@type': 'SoftwareApplication',
        name: 'Whetzy',
        applicationCategory: 'EducationalApplication',
        operatingSystem: 'Web, Android, iOS',
        inLanguage: lang,
        description: t.description,
        publisher: { '@id': `${SITE_URL}/#org` },
        offers: [offer(t.free, 0), offer(t.pro, PRO_MONTHLY_USD), offer(t.proMax, PRO_MAX_MONTHLY_USD)],
      },
    ],
  };
}

/** Para `<script type="application/ld+json">`: sin `<` crudo, que cerraría el script. */
export function serializeJsonLd(data: Record<string, unknown>): string {
  return JSON.stringify(data).replace(/</g, '\\u003c');
}
