/** Tamano del catalogo, en un solo sitio.
 *
 *  Estas cifras salen en paginas publicas (la landing y `/evidence`), asi que
 *  la seccion [4] de `scripts/check_docs.py` las compara contra
 *  `content/curriculum/tracks.json` y `content/questions/` y falla si se
 *  separan. Escribirlas a mano en un componente es lo que provoco el incidente
 *  17.12 y lo que repitio la serie 24.2: no lo hagas, importa de aqui.
 */
export const CATALOG_TRACKS = 18;
export const CATALOG_COURSES = 49;
export const CATALOG_QUESTIONS = 6233;
