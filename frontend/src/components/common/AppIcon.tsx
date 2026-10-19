/**
 * Iconos propios de Whetzy (2026-10-18), en lugar de los emoji, que cada
 * sistema dibuja distinto. Son SVG generados con IA en Canva y vectorizados
 * con `scripts/iconos/hoja_a_svg.py`; cada uno lleva su procedencia en
 * <metadata> (design/iconos/PROCEDENCIA.md). Son decorativos: el texto de al
 * lado dice lo que significan, así que van con alt="" y aria-hidden.
 */

export type GameIconName =
  | 'racha' | 'rayo' | 'trofeo' | 'oro' | 'plata' | 'bronce' | 'corona' | 'gema'
  | 'estrella' | 'confeti' | 'diana' | 'cerebro' | 'bombilla' | 'musculo'
  | 'graduacion' | 'libro';

// Los 35 tracks del catálogo con icono propio; uno nuevo usa su emoji hasta
// tener el suyo (lo vigila src/test/iconosPropios.test.tsx).
const TRACKS_CON_ICONO = new Set([
  'track01', 'track02', 'track03', 'track04', 'track05', 'track06', 'track07',
  'track08', 'track09', 'track10', 'track11', 'track12', 'track13', 'track14',
  'track15', 'track16', 'track17', 'track18', 'track19', 'track20', 'track21',
  'track22', 'track23', 'track26', 'track27', 'track28', 'track29', 'track30',
  'track40', 'track41', 'track42', 'track43', 'track44', 'track45', 'track46',
]);

interface IconProps {
  size?: number;
  className?: string;
}

function Img({ src, size = 24, className }: IconProps & { src: string }) {
  return (
    <img
      src={src}
      width={size}
      height={size}
      alt=""
      aria-hidden="true"
      draggable={false}
      className={className}
      style={{ objectFit: 'contain', verticalAlign: 'middle' }}
    />
  );
}

export function GameIcon({ name, ...rest }: IconProps & { name: GameIconName }) {
  return <Img src={`/iconos/gamificacion/${name}.svg`} {...rest} />;
}

export function TrackIcon({
  trackId,
  fallback,
  ...rest
}: IconProps & { trackId: string; fallback?: string | null }) {
  if (!TRACKS_CON_ICONO.has(trackId)) return <>{fallback ?? ''}</>;
  return <Img src={`/iconos/tracks/${trackId}.svg`} {...rest} />;
}
