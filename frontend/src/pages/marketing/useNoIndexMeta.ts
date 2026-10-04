/** Para una página reservada que todavía no tiene contenido real que valga
 *  indexar (0.14: /es/carrera, /en/career, /es/empresas, /en/enterprise).
 *
 *  No reutiliza `useDocumentMeta` (hooks/**, fuera de mi terreno,
 *  docs/SESIONES.md §4.6): ese hook está pensado para una página que SÍ
 *  quiere aparecer en buscadores con su propio canonical/OG, justo lo
 *  contrario de lo que necesita un "todavía no disponible". Esto solo pone
 *  `<meta name="robots" content="noindex">` y el título, y los deshace al
 *  desmontar. Cloudflare sigue sirviendo 200 para esta ruta (SPA fallback en
 *  `_redirects`, fuera de mi terreno) — un 404 real necesitaría que `App.tsx`
 *  (S1) deje de montar esta página; mientras tanto esto es lo que puedo
 *  hacer desde aquí. */
import { useEffect } from 'react';

export function useNoIndexMeta(title: string, lang: 'es' | 'en') {
  useEffect(() => {
    if (typeof document === 'undefined') return;
    const prevTitle = document.title;
    const prevLang = document.documentElement.lang;

    document.title = title;
    document.documentElement.lang = lang;
    let robots = document.querySelector<HTMLMetaElement>('meta[name="robots"]');
    const hadRobots = Boolean(robots);
    const prevRobotsContent = robots?.getAttribute('content') ?? '';
    if (!robots) {
      robots = document.createElement('meta');
      robots.setAttribute('name', 'robots');
      document.head.appendChild(robots);
    }
    robots.setAttribute('content', 'noindex');

    return () => {
      document.title = prevTitle;
      document.documentElement.lang = prevLang;
      if (hadRobots) robots!.setAttribute('content', prevRobotsContent);
      else robots!.remove();
    };
  }, [title, lang]);
}
