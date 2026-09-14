import { useEffect, useState } from 'react';
import { glossary as glossaryApi, type GlossaryTerm } from '../services/api';

/** Skill ids are `sk` + 2-digit track + 2-digit module + 2-digit skill. */
export function trackIdFromSkillId(skillId: string): string | null {
  const m = /^sk(\d{2})\d{4}$/.exec(skillId);
  return m ? `track${m[1]}` : null;
}

// One fetch per track for the lifetime of the tab. The glossary is small,
// immutable content, and the quiz asks for the same track many times in a row.
const cache = new Map<string, GlossaryTerm[]>();
const inFlight = new Map<string, Promise<GlossaryTerm[]>>();

async function load(trackId: string): Promise<GlossaryTerm[]> {
  const cached = cache.get(trackId);
  if (cached) return cached;

  const pending = inFlight.get(trackId);
  if (pending) return pending;

  const promise = glossaryApi
    .forTrack(trackId)
    // A track without a glossary (the certification tracks have none yet) is a
    // normal state, not an error: the quiz simply shows no highlights.
    .catch(() => [] as GlossaryTerm[])
    .then((terms) => {
      cache.set(trackId, terms);
      inFlight.delete(trackId);
      return terms;
    });

  inFlight.set(trackId, promise);
  return promise;
}

export function useGlossary(skillId: string | undefined): GlossaryTerm[] {
  const [terms, setTerms] = useState<GlossaryTerm[]>([]);

  useEffect(() => {
    const trackId = skillId ? trackIdFromSkillId(skillId) : null;
    if (!trackId) {
      setTerms([]);
      return;
    }
    let active = true;
    void load(trackId).then((t) => {
      if (active) setTerms(t);
    });
    return () => {
      active = false;
    };
  }, [skillId]);

  return terms;
}
