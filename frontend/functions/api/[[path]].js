/**
 * Cualquier /api/* que llegue al dominio del frontend es un error de
 * configuracion, y tiene que verse como tal.
 *
 * Sin esto, el fallback de SPA sirve index.html con **200** a una llamada de
 * API: el cliente intenta parsear HTML como JSON y falla en silencio, que es
 * la forma mas cara de romperse. Un 404 se ve al primer intento.
 *
 * Esto vivia en `_redirects`, pero en este proyecto de Pages **ese fichero no
 * se aplica** (comprobado el 2026-09-20: una regla explicita `/api/* ... 404`
 * devolvia 200). Como Function si corre.
 */
export function onRequest() {
  return new Response(
    '404 - esta ruta no existe en el frontend. Si esperabas la API, el origen es otro.',
    { status: 404, headers: { 'content-type': 'text/plain; charset=utf-8' } },
  );
}
