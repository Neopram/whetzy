import { useId } from 'react';

/**
 * Banderas de idioma dibujadas (ola 2, 2026-10-21). Antes eran los emoji 🇪🇸 y
 * 🇬🇧, y Windows no trae esos glifos: allí se veían las letras «ES» y «GB»
 * sueltas, o nada. Los colores son los oficiales de cada bandera, no tokens:
 * una bandera no cambia con el tema.
 */
export function LangFlag({ lang }: { lang: 'es' | 'en' }) {
  const clip = useId();
  if (lang === 'es') {
    return (
      <svg viewBox="0 0 3 2" width="20" height="14" aria-hidden="true" focusable="false" data-flag="es">
        <rect width="3" height="2" fill="#AA151B" />
        <rect y="0.5" width="3" height="1" fill="#F1BF00" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 60 30" width="20" height="14" aria-hidden="true" focusable="false" data-flag="en" preserveAspectRatio="none">
      <clipPath id={clip}>
        <path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z" />
      </clipPath>
      <rect width="60" height="30" fill="#012169" />
      <path d="M0,0 L60,30 M60,0 L0,30" stroke="#FFFFFF" strokeWidth="6" />
      <path d="M0,0 L60,30 M60,0 L0,30" clipPath={`url(#${clip})`} stroke="#C8102E" strokeWidth="4" />
      <path d="M30,0 v30 M0,15 h60" stroke="#FFFFFF" strokeWidth="10" />
      <path d="M30,0 v30 M0,15 h60" stroke="#C8102E" strokeWidth="6" />
    </svg>
  );
}
