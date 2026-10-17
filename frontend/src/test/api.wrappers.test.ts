/**
 * Método y cuerpo de cada envoltorio de services/api.ts.
 *
 * `backend/tests/test_contrato_frontend.py` ya comprueba que cada ruta del
 * cliente existe en el router, pero solo la ruta: un `PUT` cambiado a `POST`, o
 * `referral_code` renombrado a `code` en el cuerpo, pasan esa guarda y dan 405
 * o 422 en producción. Esta tabla fija las dos cosas que aquella no ve.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  API_BASE_URL,
  auth,
  certificates,
  content,
  duels,
  economy,
  exams,
  gamification,
  instructor,
  league,
  lessonsApi,
  privacy,
  progress,
  projects,
} from '../services/api';

type Caso = [nombre: string, llamada: () => Promise<unknown>, metodo: string, ruta: string, cuerpo?: unknown];

const CASOS: Caso[] = [
  ['auth.updateMe', () => auth.updateMe({ language: 'en' }), 'PATCH', '/auth/me', { language: 'en' }],
  ['auth.oauthProviders', () => auth.oauthProviders(), 'GET', '/auth/oauth/providers'],
  ['auth.setMarketingEmails', () => auth.setMarketingEmails(false), 'PATCH', '/email/preferences', { marketing: false }],
  ['auth.requestPasswordReset', () => auth.requestPasswordReset('a@b.c'), 'POST', '/auth/forgot-password', { email: 'a@b.c' }],
  ['auth.resetPassword', () => auth.resetPassword('t', 'n'), 'POST', '/auth/reset-password', { token: 't', new_password: 'n' }],
  ['progress.decaying', () => progress.decaying(3, 2), 'GET', '/progress/decaying?within_days=3&limit=2'],
  ['lessonsApi.forSkill', () => lessonsApi.forSkill('sk 1'), 'GET', '/lessons/sk%201'],
  ['economy.balance', () => economy.balance(), 'GET', '/economy/balance'],
  ['economy.prices', () => economy.prices(), 'GET', '/economy/prices'],
  ['economy.referralCode', () => economy.referralCode(), 'GET', '/economy/referral/code'],
  ['economy.redeemPromo', () => economy.redeemPromo('X'), 'POST', '/economy/promo/redeem', { code: 'X' }],
  ['economy.buyStreakFreeze', () => economy.buyStreakFreeze('r1'), 'POST', '/economy/streak-freeze', { request_id: 'r1' }],
  ['economy.activateReferral', () => economy.activateReferral('R'), 'POST', '/economy/referral/activate', { referral_code: 'R' }],
  ['league.setParticipation', () => league.setParticipation(false), 'PUT', '/league/participation', { participate: false }],
  ['gamification.badges', () => gamification.badges(), 'GET', '/badges'],
  ['duels.challenge', () => duels.challenge({ opponent_username: 'u' }), 'POST', '/duels/challenge', { opponent_username: 'u' }],
  ['duels.my', () => duels.my(), 'GET', '/duels/my'],
  [
    'duels.answer',
    () => duels.answer('d1', { question_id: 'q', selected_index: 1, response_time_ms: 5 }),
    'POST',
    '/duels/d1/answer',
    { question_id: 'q', selected_index: 1, response_time_ms: 5 },
  ],
  ['duels.join', () => duels.join('d1'), 'GET', '/duels/d1/join'],
  ['duels.result', () => duels.result('d1'), 'GET', '/duels/d1/result'],
  ['content.tracks', () => content.tracks(), 'GET', '/content/tracks'],
  ['exams.startMock', () => exams.startMock('track10'), 'POST', '/exams/mock/start', { track_id: 'track10' }],
  [
    'exams.submitMock',
    () => exams.submitMock('a1', { q1: 2 }),
    'POST',
    '/exams/mock/a1/submit',
    { answers: [{ question_id: 'q1', selected_index: 2 }] },
  ],
  ['exams.getMock', () => exams.getMock('a1'), 'GET', '/exams/mock/a1'],
  ['exams.certificationAccess', () => exams.certificationAccess('t'), 'GET', '/exams/certification/t/access'],
  ['exams.startCertifying', () => exams.startCertifying('t'), 'POST', '/exams/certification/t/start'],
  ['exams.trackBlueprint', () => exams.trackBlueprint('t'), 'GET', '/exams/track/t/blueprint'],
  ['exams.startTrackExam', () => exams.startTrackExam('t'), 'POST', '/exams/track/t/start'],
  ['exams.startTestOut', () => exams.startTestOut('m'), 'POST', '/exams/module/m/test-out/start'],
  ['exams.certificationReadiness', () => exams.certificationReadiness('t'), 'GET', '/exams/certification/t/readiness'],
  [
    'exams.submitTrackExam',
    () => exams.submitTrackExam('a2', { q2: 0 }),
    'POST',
    '/exams/track/a2/submit',
    { answers: [{ question_id: 'q2', selected_index: 0 }] },
  ],
  ['certificates.verify', () => certificates.verify('C0DE'), 'GET', '/exams/certificates/C0DE'],
  ['instructor.courses', () => instructor.courses(), 'GET', '/instructor/courses'],
  [
    'instructor.createCourse',
    () => instructor.createCourse({ title: 'T', price_cents: 900 }),
    'POST',
    '/instructor/courses',
    { title: 'T', price_cents: 900 },
  ],
  ['instructor.analytics', () => instructor.analytics(), 'GET', '/instructor/analytics'],
  ['instructor.payouts', () => instructor.payouts(), 'GET', '/instructor/payouts'],
  ['projects.list', () => projects.list('track01', 'python'), 'GET', '/projects?track_id=track01&runtime=python'],
  ['projects.list sin filtros', () => projects.list(), 'GET', '/projects'],
  ['projects.get', () => projects.get('p'), 'GET', '/projects/p'],
  ['projects.start', () => projects.start('p'), 'POST', '/projects/p/start'],
  ['projects.progress', () => projects.progress('p'), 'GET', '/projects/p/progress'],
  [
    'projects.submitStep',
    () => projects.submitStep('p', 2, 'SELECT 1;', true),
    'POST',
    '/projects/p/submit-step',
    { step_number: 2, code: 'SELECT 1;', passed: true },
  ],
  ['privacy.ccpaOptOut', () => privacy.ccpaOptOut(), 'POST', '/privacy/ccpa-opt-out'],
  ['privacy.ccpaOptIn', () => privacy.ccpaOptIn(), 'DELETE', '/privacy/ccpa-opt-out'],
  ['privacy.ccpaDisclosure', () => privacy.ccpaDisclosure(), 'GET', '/privacy/ccpa-disclosure'],
  ['privacy.rights', () => privacy.rights(), 'GET', '/privacy/rights'],
];

describe('envoltorios de services/api.ts', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockResolvedValue(new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it.each(CASOS)('%s', async (_nombre, llamada, metodo, ruta, cuerpo) => {
    await llamada();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${API_BASE_URL}${ruta}`);
    expect(init.method ?? 'GET').toBe(metodo);
    expect(init.credentials).toBe('include');
    if (cuerpo === undefined) expect(init.body).toBeUndefined();
    else expect(JSON.parse(init.body as string)).toEqual(cuerpo);
  });
});
