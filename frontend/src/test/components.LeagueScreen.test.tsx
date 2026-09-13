/**
 * Tests for src/pages/LeagueScreen.tsx — league name localization (TASK 11.10).
 *
 * The server stores a Spanish-only label on League.name ("Bronce", "Platino"),
 * and the screen used to render it verbatim, so an English user read
 * "League Platino". Red line 3 says nothing ships in one language — not one
 * string. These tests fail if that regresses.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import '../i18n';
import i18n from '../i18n';
import { LeagueScreen } from '../pages/LeagueScreen';
import { league as leagueApi } from '../services/api';

vi.mock('../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../services/api')>();
  return {
    ...actual,
    league: { current: vi.fn() },
  };
});

const currentMock = leagueApi.current as unknown as ReturnType<typeof vi.fn>;

/** Every Spanish league label the seeder writes to League.name. */
const SPANISH_LABELS = ['Bronce', 'Plata', 'Oro', 'Platino', 'Diamante'];

function standings(tier: string, name: string) {
  return {
    league: { id: tier, name, tier, min_xp: 0 },
    week_start: '2026-03-09',
    standings: [
      {
        rank: 1,
        user_id: 'u1',
        username: 'ana',
        display_name: 'Ana',
        avatar_emoji: '🦊',
        xp_earned: 120,
        is_current_user: true,
      },
    ],
    promotion_zone: 5,
    demotion_zone: 5,
  };
}

describe('LeagueScreen — league name localization', () => {
  beforeEach(() => {
    currentMock.mockReset();
  });

  afterEach(async () => {
    cleanup();
    await i18n.changeLanguage('es');
  });

  it.each([
    ['bronze', 'Bronce', 'Bronze'],
    ['silver', 'Plata', 'Silver'],
    ['gold', 'Oro', 'Gold'],
    ['platinum', 'Platino', 'Platinum'],
    ['diamond', 'Diamante', 'Diamond'],
  ])('renders %s in English, ignoring the Spanish server label', async (tier, esLabel, enLabel) => {
    await i18n.changeLanguage('en');
    currentMock.mockResolvedValue(standings(tier, esLabel));

    render(<LeagueScreen />);

    const heading = await screen.findByRole('heading', { level: 1 });
    expect(heading.textContent).toContain(enLabel);
    expect(heading.textContent).not.toContain(esLabel);
  });

  it('renders the Spanish name for Spanish users', async () => {
    await i18n.changeLanguage('es');
    currentMock.mockResolvedValue(standings('platinum', 'Platino'));

    render(<LeagueScreen />);

    const heading = await screen.findByRole('heading', { level: 1 });
    expect(heading.textContent).toContain('Platino');
  });

  it('shows no Spanish league label anywhere in the English UI', async () => {
    await i18n.changeLanguage('en');
    currentMock.mockResolvedValue(standings('diamond', 'Diamante'));

    const { container } = render(<LeagueScreen />);
    await screen.findByRole('heading', { level: 1 });

    for (const label of SPANISH_LABELS) {
      expect(container.textContent).not.toContain(label);
    }
  });

  it('falls back to the server name for a tier the client does not know', async () => {
    // A new tier shipped by the backend before the client has a key for it
    // should still render something, not an empty heading or a raw i18n key.
    await i18n.changeLanguage('en');
    currentMock.mockResolvedValue(standings('obsidian', 'Obsidiana'));

    render(<LeagueScreen />);

    const heading = await screen.findByRole('heading', { level: 1 });
    expect(heading.textContent).toContain('Obsidiana');
    expect(heading.textContent).not.toContain('league.tiers');
  });

  it('never renders a raw i18n key', async () => {
    await i18n.changeLanguage('en');
    currentMock.mockResolvedValue(standings('gold', 'Oro'));

    const { container } = render(<LeagueScreen />);
    await screen.findByRole('heading', { level: 1 });

    expect(container.textContent).not.toMatch(/league\.[a-z]/i);
  });

  it('keeps both locales complete for every seeded tier', async () => {
    for (const tier of ['bronze', 'silver', 'gold', 'platinum', 'diamond']) {
      for (const lng of ['es', 'en']) {
        expect(
          i18n.getFixedT(lng)(`league.tiers.${tier}`),
          `missing league.tiers.${tier} in ${lng}`,
        ).not.toBe(`league.tiers.${tier}`);
      }
    }
  });

  it('shows the empty state when the API fails', async () => {
    await i18n.changeLanguage('en');
    currentMock.mockRejectedValue(new Error('offline'));

    render(<LeagueScreen />);

    await waitFor(() => {
      expect(screen.getByText(i18n.t('league.empty'))).toBeTruthy();
    });
  });
});
