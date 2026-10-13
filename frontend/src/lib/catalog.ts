/** Tamano del catalogo, en un solo sitio.
 *
 *  Estas cifras salen en paginas publicas (la landing y `/evidence`), asi que
 *  la seccion [4] de `scripts/check_docs.py` las compara contra
 *  `content/curriculum/tracks.json` y `content/questions/` y falla si se
 *  separan. Escribirlas a mano en un componente es lo que provoco el incidente
 *  17.12 y lo que repitio la serie 24.2: no lo hagas, importa de aqui.
 */
export const CATALOG_TRACKS = 35;
/** Curso = módulo del molde (ADR-46, 37.2); antes «track × nivel» (49). Solo es unidad de
 *  presentación: el plan del catálogo mide skills y temario (ADR-53). */
export const CATALOG_COURSES = 174;
export const CATALOG_QUESTIONS = 12037;
