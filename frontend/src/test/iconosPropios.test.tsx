/**
 * Iconos propios (2026-10-18): sustituyen a los emoji, que cada sistema
 * dibuja distinto. Son SVG generados con IA en Canva y vectorizados; los
 * términos de Canva prohíben quitar la procedencia del contenido generado con
 * IA, así que cada SVG la lleva en <metadata> (design/iconos/PROCEDENCIA.md).
 */
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { GameIcon, TrackIcon } from '../components/common/AppIcon';

const ICONOS = join(process.cwd(), 'public', 'iconos');
const tracks: { id: string }[] = JSON.parse(
  readFileSync(join(process.cwd(), '..', 'content', 'curriculum', 'tracks.json'), 'utf-8'),
).tracks;

describe('iconos propios', () => {
  it('cada track del catálogo tiene su SVG', () => {
    const svgs = new Set(readdirSync(join(ICONOS, 'tracks')));
    const sinIcono = tracks.map((t) => t.id).filter((id) => !svgs.has(`${id}.svg`));
    expect(sinIcono).toEqual([]);
  });

  it('cada SVG lleva su procedencia y un viewBox', () => {
    for (const dir of ['tracks', 'gamificacion']) {
      for (const f of readdirSync(join(ICONOS, dir)).filter((n) => n.endsWith('.svg'))) {
        const svg = readFileSync(join(ICONOS, dir, f), 'utf-8');
        expect(svg, `${dir}/${f}`).toMatch(/<metadata>[^<]*generado_con_ia[^<]*canva_media_id/);
        expect(svg, `${dir}/${f}`).toMatch(/<svg[^>]*viewBox=/);
      }
    }
  });

  it('TrackIcon pinta el SVG del track y, si no hay, el emoji de respaldo', () => {
    const { container, rerender } = render(<TrackIcon trackId="track01" fallback="🐍" />);
    const img = container.querySelector('img');
    expect(img?.getAttribute('src')).toBe('/iconos/tracks/track01.svg');
    expect(img?.getAttribute('alt')).toBe('');
    rerender(<TrackIcon trackId="track99" fallback="📘" />);
    expect(container.querySelector('img')).toBeNull();
    expect(container.textContent).toBe('📘');
  });

  it('GameIcon pinta el SVG de gamificación, decorativo', () => {
    const { container } = render(<GameIcon name="racha" size={20} />);
    const img = container.querySelector('img');
    expect(img?.getAttribute('src')).toBe('/iconos/gamificacion/racha.svg');
    expect(img?.getAttribute('aria-hidden')).toBe('true');
    expect(img?.getAttribute('width')).toBe('20');
  });

  it('las pantallas ya no usan los emoji de gamificación que tienen icono propio', () => {
    const pantallas = [
      'LeagueScreen', 'PlacementScreen', 'PublicProfileScreen', 'LessonScreen', 'ProjectScreen',
    ];
    const emoji = /🔥|🏆|🥇|🥈|🥉|👑|💎|⭐|🎉|🎯|🧠|💡|💪|🎓|📚/u;
    for (const p of pantallas) {
      const src = readFileSync(join(process.cwd(), 'src', 'pages', `${p}.tsx`), 'utf-8');
      expect(src, p).not.toMatch(emoji);
    }
  });
});
