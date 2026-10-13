import { useId } from 'react';

interface BrandMarkProps {
  /** Alto en px; el ancho sale de la proporción del símbolo (135 × 110). */
  height?: number;
  /** Si el símbolo va solo, sin el nombre al lado, dale un nombre accesible. */
  title?: string;
}

/**
 * Símbolo de Whetzy (design/brand/whetzy-mark.svg) en línea: corchetes de
 * código, la W y la línea que sube hasta el punto. En línea y no como <img>
 * para que no cueste una petición en la barra superior ni en la landing
 * pre-renderizada. Los id del degradado y de los filtros salen de useId: dos
 * símbolos en la misma página no se pisan los <defs>.
 */
export function BrandMark({ height = 24, title }: BrandMarkProps) {
  const id = useId().replace(/[^\w-]/g, '');
  const main = `${id}-main`;
  const dot = `${id}-dot`;
  const glow = `${id}-glow`;
  const softGlow = `${id}-soft`;
  return (
    <svg
      viewBox="-10 -10 135 110"
      width={Math.round((height * 135) / 110)}
      height={height}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      focusable="false"
    >
      <defs>
        <linearGradient id={main} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00BFFF" />
          <stop offset="40%" stopColor="#7B68EE" />
          <stop offset="70%" stopColor="#C71585" />
          <stop offset="100%" stopColor="#FF1493" />
        </linearGradient>
        <radialGradient id={dot} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FF69B4" />
          <stop offset="50%" stopColor="#FF1493" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#FF1493" stopOpacity="0" />
        </radialGradient>
        <filter id={glow} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id={softGlow} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="8" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <g fill="none" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 20 L0 55 L20 90" stroke="#00BFFF" />
        <path d="M15 55 L30 90 L50 50 L70 90 L90 30" stroke={`url(#${main})`} />
        <path d="M95 20 L115 55 L95 90" stroke="#FF1493" />
      </g>
      <line x1="70" y1="90" x2="100" y2="10" stroke={`url(#${main})`} strokeWidth="7" strokeLinecap="round" filter={`url(#${glow})`} />
      <circle cx="100" cy="10" r="10" fill={`url(#${dot})`} filter={`url(#${softGlow})`} />
      <circle cx="100" cy="10" r="6" fill="#FFFFFF" fillOpacity="0.9" />
      <circle cx="100" cy="10" r="3" fill="#FF1493" />
    </svg>
  );
}
