/**
 * Ninguna cadena visible se queda en un solo idioma.
 *
 * `t('landing.start', 'Comienza gratis')` devuelve el segundo argumento cuando
 * la clave no existe **en ningun idioma**. Eso hacia que la aplicacion pareciera
 * traducida y que un usuario en ingles viera español en la portada, en las
 * lecciones, en el perfil publico y en el onboarding — incluida, con ironia, la
 * pantalla de «elige tu idioma». Treinta y una cadenas, invisibles para
 * cualquiera que probara en español. ADR-17: ES y EN sin mezclar.
 *
 * El texto por defecto sigue siendo util como red de seguridad; lo que no puede
 * es ser la unica version de la cadena.
 */

import { readdirSync, readFileSync, type Dirent } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const SRC = join(RAIZ, 'src')

/**
 * Ya no hay excepciones: los tres paneles que existian sin que nadie los
 * importara (`B2BPanel`, `CertificationPanel`, `GamificationPanel`) se
 * borraron el 2026-09-20. Eran maquetas estaticas con datos inventados
 * dentro, y la de certificacion duplicaba el simulacro que ya funciona de
 * verdad desde Rutas.
 *
 * Si alguna vez vuelve a hacer falta una excepcion, la lista es el sitio —
 * pero que crezca significa que hay codigo muerto, no que falte traducir.
 */
const NO_ALCANZABLES: string[] = []

function ficheros(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e: Dirent) => {
    const p = join(dir, e.name)
    if (e.isDirectory()) return e.name === 'test' ? [] : ficheros(p)
    return /\.tsx?$/.test(e.name) ? [p] : []
  })
}

function aplanar(d: Record<string, unknown>, pre = ''): Record<string, string> {
  const out: Record<string, string> = {}
  for (const [k, v] of Object.entries(d)) {
    const kk = `${pre}${k}`
    if (v && typeof v === 'object') Object.assign(out, aplanar(v as Record<string, unknown>, `${kk}.`))
    else out[kk] = String(v)
  }
  return out
}

const ES = aplanar(JSON.parse(readFileSync(join(SRC, 'i18n/es/common.json'), 'utf8')))
const EN = aplanar(JSON.parse(readFileSync(join(SRC, 'i18n/en/common.json'), 'utf8')))

/** i18next v26 pluraliza con `_one` / `_other`, no con `_plural`. */
const tiene = (mapa: Record<string, string>, k: string) =>
  k in mapa || Object.keys(mapa).some((x) => x.startsWith(`${k}_`))

function clavesUsadas(): Map<string, string[]> {
  const uso = new Map<string, string[]>()
  for (const f of ficheros(SRC)) {
    const rel = f.slice(SRC.length + 1).replace(/\\/g, '/')
    if (NO_ALCANZABLES.includes(rel)) continue
    const texto = readFileSync(f, 'utf8')
    for (const m of texto.matchAll(/\bt\(\s*['"]([a-zA-Z0-9_.]+)['"]/g)) {
      uso.set(m[1], [...(uso.get(m[1]) ?? []), rel])
    }
  }
  return uso
}

describe('cobertura de traducciones', () => {
  it('encuentra claves que comprobar', () => {
    expect(clavesUsadas().size).toBeGreaterThan(300)
  })

  it('toda clave de una pantalla alcanzable existe en ES y EN', () => {
    const faltan: string[] = []
    for (const [clave, donde] of clavesUsadas()) {
      const sinEs = !tiene(ES, clave)
      const sinEn = !tiene(EN, clave)
      if (sinEs || sinEn) {
        const cual = sinEs && sinEn ? 'ES y EN' : sinEs ? 'ES' : 'EN'
        faltan.push(`${clave} (falta en ${cual}) — ${donde[0]}`)
      }
    }
    expect(faltan, 'un texto por defecto en el codigo no sustituye a una traduccion').toEqual([])
  })

  it('los dos idiomas tienen exactamente las mismas claves', () => {
    const soloEs = Object.keys(ES).filter((k) => !(k in EN))
    const soloEn = Object.keys(EN).filter((k) => !(k in ES))
    expect({ soloEs, soloEn }).toEqual({ soloEs: [], soloEn: [] })
  })

  it('ninguna cadena inglesa se quedo copiada del español', () => {
    // Heuristica barata contra el copia-pega: caracteres que el ingles no usa.
    const sospechosas = Object.entries(EN)
      .filter(([, v]) => /[áéíóúñ¿¡]/i.test(v))
      .map(([k, v]) => `${k}: ${v}`)
    expect(sospechosas).toEqual([])
  })
})
