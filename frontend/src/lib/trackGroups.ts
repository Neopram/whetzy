/**
 * 43.3 (ADR-65 D2): el onboarding enseña los tracks de aprendizaje agrupados
 * por área y, al elegir uno, las certificaciones relacionadas.
 *
 * Desde la ola 2 (2026-10-21) los mismos cinco grupos son los campos del
 * catálogo, y cada certificación tiene el suyo en `CERT_FIELDS`.
 *
 * Los ids salen de `content/curriculum/tracks.json`; `trackGroups.test.ts`
 * comprueba que cada track de aprendizaje está en un grupo y solo en uno, y
 * que cada certificación nombrada existe y lo es.
 */

export type TrackGroupId = 'programming' | 'software' | 'dataAi' | 'cloudInfra' | 'security';

export const TRACK_GROUPS: { id: TrackGroupId; tracks: string[] }[] = [
  { id: 'programming', tracks: ['track01', 'track02', 'track03', 'track16', 'track26'] },
  { id: 'software', tracks: ['track04', 'track05', 'track14', 'track28', 'track29', 'track30'] },
  { id: 'dataAi', tracks: ['track06', 'track07', 'track12', 'track20', 'track21', 'track27'] },
  { id: 'cloudInfra', tracks: ['track15', 'track18', 'track19', 'track22', 'track23'] },
  { id: 'security', tracks: ['track13', 'track17'] },
];

/** Campo de cada certificación en el catálogo (ola 2). */
export const CERT_FIELDS: Record<string, TrackGroupId> = {
  track09: 'programming',
  track41: 'programming',
  track11: 'dataAi',
  track43: 'dataAi',
  track45: 'dataAi',
  track46: 'dataAi',
  track08: 'cloudInfra',
  track10: 'cloudInfra',
  track44: 'cloudInfra',
  track40: 'security',
  track42: 'security',
};

const FIELD_OF: Record<string, TrackGroupId> = {
  ...Object.fromEntries(TRACK_GROUPS.flatMap((g) => g.tracks.map((id) => [id, g.id] as const))),
  ...CERT_FIELDS,
};

/** Campo de una ruta del catálogo; `undefined` si es una ruta nueva sin asignar. */
export function fieldOf(trackId: string): TrackGroupId | undefined {
  return FIELD_OF[trackId];
}

const PYTHON_CERTS = ['track09', 'track41'];
const AI_CERTS = ['track11', 'track45', 'track43'];
const SECURITY_CERTS = ['track40', 'track42'];
const AWS_CERTS = ['track08', 'track10'];
const DATA_CERTS = ['track46', 'track43'];

/** Certificaciones que tienen sentido junto a cada track de aprendizaje. */
export const RELATED_CERTS: Record<string, string[]> = {
  track01: PYTHON_CERTS,
  track02: PYTHON_CERTS,
  track03: PYTHON_CERTS,
  track06: AI_CERTS,
  track07: AI_CERTS,
  track12: DATA_CERTS,
  track20: DATA_CERTS,
  track21: DATA_CERTS,
  track27: ['track46'],
  track13: SECURITY_CERTS,
  track17: SECURITY_CERTS,
  track15: AWS_CERTS,
  track18: AWS_CERTS,
  track19: AWS_CERTS,
  track22: ['track44', 'track45', 'track46'],
};

export function relatedCerts(trackId: string): string[] {
  return RELATED_CERTS[trackId] ?? [];
}
