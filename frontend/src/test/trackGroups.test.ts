import { describe, expect, it } from 'vitest';
import tracksJson from '../../../content/curriculum/tracks.json';
import { CERT_FIELDS, RELATED_CERTS, TRACK_GROUPS, fieldOf } from '../lib/trackGroups';

interface TrackDef { id: string; is_certification?: boolean }
const tracks = (tracksJson as { tracks: TrackDef[] }).tracks;
const learning = tracks.filter((t) => !t.is_certification).map((t) => t.id);
const certs = new Set(tracks.filter((t) => t.is_certification).map((t) => t.id));

describe('grupos de tracks del onboarding (43.3, D2)', () => {
  it('cada track de aprendizaje está en un grupo y solo en uno', () => {
    const grouped = TRACK_GROUPS.flatMap((g) => g.tracks);
    expect(new Set(grouped).size).toBe(grouped.length);
    expect([...grouped].sort()).toEqual([...learning].sort());
    expect(learning).toHaveLength(24);
  });

  it('las certificaciones relacionadas existen y son de certificación', () => {
    for (const [trackId, list] of Object.entries(RELATED_CERTS)) {
      expect(learning, trackId).toContain(trackId);
      for (const c of list) expect(certs.has(c), `${trackId} → ${c}`).toBe(true);
    }
  });
});

describe('campos del catálogo (ola 2)', () => {
  it('cada certificación tiene campo, y solo las certificaciones están en CERT_FIELDS', () => {
    expect(Object.keys(CERT_FIELDS).sort()).toEqual([...certs].sort());
  });

  it('toda ruta del catálogo tiene exactamente un campo de los cinco', () => {
    const ids = new Set(TRACK_GROUPS.map((g) => g.id));
    for (const t of tracks) expect(ids.has(fieldOf(t.id)!), t.id).toBe(true);
  });
});
