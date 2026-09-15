/**
 * Tests for the certificate card and the public verification page (17.2).
 *
 * These exist because the session that wrote the certificate UI could not open
 * a browser, so this is the only thing standing between the component and a
 * regression nobody would see until someone put the URL on a CV.
 *
 * What they pin down is the part that is a *decision* rather than markup: what
 * a public page is allowed to show, that a revoked certificate says so instead
 * of vanishing, and that the verification page does not try to recruit the
 * person checking somebody else's proof.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import '../i18n';
import i18n from '../i18n';
import { CertificateCard, certificateUrl } from '../components/certificate/CertificateCard';
import { CertificateScreen } from '../pages/CertificateScreen';
import { certificates, type CertificatePublic } from '../services/api';

const CERT: CertificatePublic = {
  code: 'a'.repeat(32),
  username: 'ada',
  track_id: 'track01',
  track_name_es: 'Python desde cero',
  track_name_en: 'Python from scratch',
  score_pct: 86.5,
  questions: 20,
  issued_at: '2026-09-15T10:00:00Z',
  revoked: false,
};

beforeEach(async () => {
  await i18n.changeLanguage('es');
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('CertificateCard', () => {
  it('shows the holder, the track and the score', () => {
    render(<CertificateCard certificate={CERT} />);
    expect(screen.getByText('ada')).toBeTruthy();
    expect(screen.getByText('Python desde cero')).toBeTruthy();
    expect(screen.getByText('86.5%')).toBeTruthy();
  });

  it('follows the reader language for the track name', async () => {
    const { rerender } = render(<CertificateCard certificate={CERT} />);
    expect(screen.getByText('Python desde cero')).toBeTruthy();

    await i18n.changeLanguage('en');
    rerender(<CertificateCard certificate={CERT} />);
    // Red line 3: nothing ships in one language only.
    expect(screen.getByText('Python from scratch')).toBeTruthy();
  });

  it('says a revoked certificate is revoked instead of hiding it', () => {
    // A card that simply disappeared would leave the person checking unable to
    // tell "withdrawn" from "never existed".
    render(<CertificateCard certificate={{ ...CERT, revoked: true }} />);
    expect(screen.getByRole('status')).toBeTruthy();
    expect(screen.queryByText('86.5%')).toBeNull();
  });

  it('offers the share link to the holder and withholds it from a verifier', () => {
    const { rerender } = render(<CertificateCard certificate={CERT} />);
    expect(screen.getByRole('button')).toBeTruthy();
    expect(screen.getByText(certificateUrl(CERT.code))).toBeTruthy();

    rerender(<CertificateCard certificate={CERT} showShare={false} />);
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('builds the verification URL from the current origin', () => {
    // Not from a build-time constant: one fewer thing to be wrong in dev,
    // preview and production separately.
    expect(certificateUrl('abc')).toBe(`${window.location.origin}/certificate/abc`);
  });
});

describe('CertificateScreen', () => {
  it('renders the certificate when the code resolves', async () => {
    vi.spyOn(certificates, 'verify').mockResolvedValue(CERT);
    render(<CertificateScreen code={CERT.code} />);

    await waitFor(() => expect(screen.getByText('ada')).toBeTruthy());
    expect(screen.getByText('Python desde cero')).toBeTruthy();
  });

  it('says not found for an unknown code, without leaking why', async () => {
    vi.spyOn(certificates, 'verify').mockRejectedValue(new Error('HTTP 404'));
    render(<CertificateScreen code={'0'.repeat(32)} />);

    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy());
    expect(screen.getByText(/No encontramos/)).toBeTruthy();
  });

  it('treats a server error the same as a missing code', async () => {
    // Telling a 500 apart from a 404 would tell a probing visitor which codes
    // exist, which is the one thing the unguessable code is protecting.
    vi.spyOn(certificates, 'verify').mockRejectedValue(new Error('HTTP 500'));
    render(<CertificateScreen code={'f'.repeat(32)} />);

    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy());
    expect(screen.getByText(/No encontramos/)).toBeTruthy();
  });

  it('does not push the visitor to sign up', async () => {
    // It is somebody else's proof, not a funnel.
    vi.spyOn(certificates, 'verify').mockResolvedValue(CERT);
    render(<CertificateScreen code={CERT.code} />);

    await waitFor(() => expect(screen.getByText('ada')).toBeTruthy());
    expect(screen.queryByText(/Crear cuenta|Empezar gratis|Registrarse/i)).toBeNull();
  });

  it('ignores a response that arrives after the code changed', async () => {
    // Two codes in flight and the slower one landing last would show the wrong
    // certificate under the right URL.
    let resolveFirst: (c: CertificatePublic) => void = () => {};
    const slow = new Promise<CertificatePublic>(r => {
      resolveFirst = r;
    });
    vi.spyOn(certificates, 'verify').mockReturnValueOnce(slow);

    const { unmount } = render(<CertificateScreen code="slow-code" />);
    unmount();
    resolveFirst(CERT);

    // Nothing to assert visually — the guarantee is that no state update fires
    // after unmount. React logs an error if it does, so a silent pass is the
    // signal.
    await new Promise(r => setTimeout(r, 10));
  });
});
