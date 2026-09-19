/**
 * Currency configuration by language segment (Series 23.2).
 * EUR for Spanish (ES), USD for English (EN).
 */

export type Language = 'es' | 'en';
export type Currency = 'EUR' | 'USD';

const CURRENCY_BY_LANGUAGE: Record<Language, Currency> = {
  es: 'EUR',
  en: 'USD',
};

const CURRENCY_SYMBOL: Record<Currency, string> = {
  EUR: '€',
  USD: '$',
};

export function getCurrencyForLanguage(language: Language): Currency {
  return CURRENCY_BY_LANGUAGE[language] || 'EUR';
}

export function getCurrencySymbol(currency: Currency): string {
  return CURRENCY_SYMBOL[currency] || '€';
}

export interface PricingPlan {
  /** Free/Plus/Pro */
  name: string;
  /** e.g., 9.99 or 19.99 */
  amount: number;
  currency: Currency;
  period: string;
  features: string[];
  highlighted?: boolean;
}

/**
 * Get pricing in the specified currency. Prices are in EUR by default;
 * USD equivalents assume 1 EUR = 1.10 USD (configure as needed).
 */
export function getPricingPlans(language: Language): PricingPlan[] {
  const currency = getCurrencyForLanguage(language);
  const isSpanish = language === 'es';

  const eurPrices = {
    plus: 9.99,
    pro: 19.99,
  };

  const usdPrices = {
    plus: 10.99,
    pro: 21.99,
  };

  const prices = currency === 'EUR' ? eurPrices : usdPrices;
  const periodText = isSpanish ? 'mes' : 'month';

  return [
    {
      name: isSpanish ? 'Gratis' : 'Free',
      amount: 0,
      currency,
      period: periodText,
      features: isSpanish
        ? ['1 track de contenido', 'Quiz adaptativo básico', 'Modo estudio ilimitado', 'Glosario bilingüe']
        : ['1 content track', 'Basic adaptive quiz', 'Unlimited study mode', 'Bilingual glossary'],
    },
    {
      name: 'Plus',
      amount: prices.plus,
      currency,
      period: periodText,
      features: isSpanish
        ? [
            'Todos los tracks',
            'Modo examen y repaso',
            'Tutor con IA (explicaciones)',
            'Ligas semanales',
            'Duelos en tiempo real',
            'Sin anuncios',
          ]
        : [
            'All tracks',
            'Exam and review modes',
            'AI tutor (explanations)',
            'Weekly leagues',
            'Real-time duels',
            'No ads',
          ],
      highlighted: true,
    },
    {
      name: 'Pro',
      amount: prices.pro,
      currency,
      period: periodText,
      features: isSpanish
        ? ['Todo lo de Plus', 'Historial de analytics', 'Acceso anticipado a nuevos tracks', 'Soporte prioritario']
        : ['Everything in Plus', 'Analytics history', 'Early access to new tracks', 'Priority support'],
    },
  ];
}

/**
 * Format price for display (e.g., "9,99€" in ES or "$10.99" in EN).
 */
export function formatPrice(amount: number, currency: Currency, language: Language): string {
  if (amount === 0) return '0';

  const symbol = getCurrencySymbol(currency);
  const isSpanish = language === 'es';

  if (isSpanish && currency === 'EUR') {
    // Spanish format: 9,99€
    return `${amount.toFixed(2).replace('.', ',').replace(',', ',').slice(0, -1)},${
      amount.toFixed(2).split('.')[1]
    }€`;
  }
  // English format: $9.99
  return `${symbol}${amount.toFixed(2)}`;
}
