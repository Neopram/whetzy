/**
 * Tests for src/hooks/useGlossary.ts
 *
 * trackIdFromSkillId already has coverage via components.GlossaryText.test.tsx;
 * this file focuses on the useGlossary hook itself — fetching, the
 * per-track cache, in-flight de-duplication, the "no glossary yet" fallback,
 * and cleanup on unmount — none of which had a single test before.
 *
 * The module-level `cache`/`inFlight` maps in useGlossary.ts persist for the
 * life of the test file, so each test below uses its own track number
 * (via a distinct sk-prefix) to avoid bleeding state between tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useGlossary } from '../hooks/useGlossary';
import type { GlossaryTerm } from '../services/api';

vi.mock('../services/api', () => ({
  glossary: { forTrack: vi.fn() },
}));

import { glossary } from '../services/api';

const term = (trackId: string, over: Partial<GlossaryTerm> & { id: string }): GlossaryTerm => ({
  track_id: trackId,
  term_es: 'termino',
  term_en: 'term',
  definition_es: 'def es',
  definition_en: 'def en',
  source: null,
  order: 1,
  ...over,
});

describe('useGlossary', () => {
  beforeEach(() => {
    vi.mocked(glossary.forTrack).mockReset();
  });

  it('returns no terms and never fetches when skillId is undefined', () => {
    const { result } = renderHook(() => useGlossary(undefined));
    expect(result.current).toEqual([]);
    expect(glossary.forTrack).not.toHaveBeenCalled();
  });

  it('returns no terms and never fetches for a skillId with no derivable track', () => {
    const { result } = renderHook(() => useGlossary('not-a-skill-id'));
    expect(result.current).toEqual([]);
    expect(glossary.forTrack).not.toHaveBeenCalled();
  });

  it('fetches and returns the glossary terms for the derived track', async () => {
    const terms = [term('track90', { id: 't90-1' })];
    vi.mocked(glossary.forTrack).mockResolvedValue(terms);

    const { result } = renderHook(() => useGlossary('sk900101'));
    await waitFor(() => expect(result.current).toEqual(terms));
    expect(glossary.forTrack).toHaveBeenCalledWith('track90');
  });

  it('falls back to an empty array when the track has no glossary yet (request rejects)', async () => {
    vi.mocked(glossary.forTrack).mockRejectedValue(new Error('404'));

    const { result } = renderHook(() => useGlossary('sk910101'));
    await waitFor(() => expect(glossary.forTrack).toHaveBeenCalledWith('track91'));
    // The hook must swallow the rejection, not throw — and terms stay [].
    expect(result.current).toEqual([]);
  });

  it('caches per track: a second hook for the same track does not refetch', async () => {
    const terms = [term('track92', { id: 't92-1' })];
    vi.mocked(glossary.forTrack).mockResolvedValue(terms);

    const { result: first } = renderHook(() => useGlossary('sk920101'));
    await waitFor(() => expect(first.current).toEqual(terms));

    const { result: second } = renderHook(() => useGlossary('sk920202'));
    await waitFor(() => expect(second.current).toEqual(terms));

    expect(glossary.forTrack).toHaveBeenCalledTimes(1);
  });

  it('de-dupes concurrent requests for the same in-flight track', async () => {
    let resolveFetch!: (v: GlossaryTerm[]) => void;
    vi.mocked(glossary.forTrack).mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve;
      })
    );
    const terms = [term('track93', { id: 't93-1' })];

    const { result: first } = renderHook(() => useGlossary('sk930101'));
    const { result: second } = renderHook(() => useGlossary('sk930202'));

    resolveFetch(terms);

    await waitFor(() => expect(first.current).toEqual(terms));
    await waitFor(() => expect(second.current).toEqual(terms));
    expect(glossary.forTrack).toHaveBeenCalledTimes(1);
  });

  it('does not update state (or warn) after unmount', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    let resolveFetch!: (v: GlossaryTerm[]) => void;
    vi.mocked(glossary.forTrack).mockReturnValue(
      new Promise((resolve) => {
        resolveFetch = resolve;
      })
    );

    const { unmount } = renderHook(() => useGlossary('sk940101'));
    unmount();
    resolveFetch([term('track94', { id: 't94-1' })]);
    // Let the resolved microtask flush.
    await new Promise((r) => setTimeout(r, 0));

    expect(errorSpy).not.toHaveBeenCalled();
    errorSpy.mockRestore();
  });

  it('refetches when skillId changes to a different track', async () => {
    vi.mocked(glossary.forTrack).mockImplementation((trackId: string) =>
      Promise.resolve([term(trackId, { id: `${trackId}-1` })])
    );

    const { result, rerender } = renderHook(({ skillId }) => useGlossary(skillId), {
      initialProps: { skillId: 'sk950101' as string | undefined },
    });
    await waitFor(() => expect(result.current[0]?.track_id).toBe('track95'));

    rerender({ skillId: 'sk960101' });
    await waitFor(() => expect(result.current[0]?.track_id).toBe('track96'));

    expect(glossary.forTrack).toHaveBeenCalledWith('track95');
    expect(glossary.forTrack).toHaveBeenCalledWith('track96');
  });

  it('resets to no terms when skillId becomes undefined', async () => {
    const terms = [term('track97', { id: 't97-1' })];
    vi.mocked(glossary.forTrack).mockResolvedValue(terms);

    const { result, rerender } = renderHook(({ skillId }) => useGlossary(skillId), {
      initialProps: { skillId: 'sk970101' as string | undefined },
    });
    await waitFor(() => expect(result.current).toEqual(terms));

    rerender({ skillId: undefined });
    await waitFor(() => expect(result.current).toEqual([]));
  });
});
