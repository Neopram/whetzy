/**
 * Estructura de la landing (2026-10-15): lo que la maqueta del dueño traía mal
 * y no debe volver — dos respuestas correctas en la pregunta de ejemplo,
 * enlaces a ninguna parte en el footer — y lo que promete: FAQ completa y
 * bandas en vez de porcentaje.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import i18n from '../i18n';
import LandingScreen from '../pages/LandingScreen';
import { MOCK_CORRECT, MOCK_OPTIONS } from '../components/landing/HeroQuizMock';
import { MOCK_DOMAINS } from '../components/landing/ReadinessBandsMock';
import { COMPARISON_COMPETITORS } from '../lib/comparison';

describe.each(['es', 'en'] as const)('landing (%s)', (lang) => {
  const setup = async () => {
    await i18n.changeLanguage(lang);
    return render(<LandingScreen />);
  };

  it('la pregunta de ejemplo tiene exactamente una correcta', async () => {
    const { container } = await setup();
    expect(container.querySelectorAll('[data-correct="true"]')).toHaveLength(1);
    expect(MOCK_OPTIONS[MOCK_CORRECT]).toBe(String('Python'.length));
  });

  it('las seis preguntas frecuentes tienen respuesta', async () => {
    const { container } = await setup();
    const items = container.querySelectorAll('#faq details');
    expect(items).toHaveLength(6);
    items.forEach((d) => expect(d.querySelector('p')?.textContent?.length ?? 0).toBeGreaterThan(20));
  });

  it('la preparación son bandas que suman los pesos del examen, sin % global', async () => {
    await setup();
    expect(MOCK_DOMAINS.reduce((a, d) => a + d.weight, 0)).toBe(100);
    expect(screen.getAllByText(i18n.t('bands.insufficient')).length).toBeGreaterThan(0);
  });

  it('ningún enlace va a "#" a secas', async () => {
    const { container } = await setup();
    container.querySelectorAll('a').forEach((a) => expect(a.getAttribute('href')).not.toBe('#'));
  });

  it('la comparativa solo nombra competidores comprobados', async () => {
    const { container } = await setup();
    const heads = [...container.querySelectorAll('#compare thead th')].map((th) => th.textContent).filter(Boolean);
    expect(heads).toEqual(['Whetzy', ...COMPARISON_COMPETITORS]);
  });
});
