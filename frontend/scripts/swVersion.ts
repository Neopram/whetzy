/**
 * `public/sw.js` llevaba su `VERSION` como una fecha escrita a mano
 * (`v2-2026-09-19`) — nada en el build la tocaba, así que un deploy que
 * cambiara la lógica del propio service worker sin que alguien se acordara
 * de subir esa fecha dejaba `CACHE_NAME` igual que antes: el `activate` que
 * borra "cualquier caché cuyo nombre no coincida" no borraba ninguna,
 * exactamente el bug que el comentario de cabecera de sw.js describe que ya
 * pasó una vez con la constante vieja `whetzy-v1` (0.15).
 *
 * `vite.config.ts` ya resuelve el commit real del build para el
 * `<meta name="whetzy-build">` que usa `check-deployed.mjs` — este módulo
 * reutiliza ese mismo valor en vez de inventar un segundo mecanismo.
 */
export const SW_VERSION_PLACEHOLDER = '__WHETZY_BUILD_SHA__';

/** Sustituye el placeholder de `public/sw.js` por el commit real del build.
 *  Revienta si no lo encuentra: mejor que el build falle a que vuelva a
 *  colarse una fecha escrita a mano sin que nadie la reemplace jamás. */
export function injectBuildVersion(source: string, sha: string): string {
  if (!source.includes(SW_VERSION_PLACEHOLDER)) {
    throw new Error(
      `[sw-version] sw.js no contiene ${SW_VERSION_PLACEHOLDER} -- ` +
        '¿se ha vuelto a escribir una versión a mano en vez del placeholder?'
    );
  }
  return source.split(SW_VERSION_PLACEHOLDER).join(sha);
}
