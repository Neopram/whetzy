import { readdirSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

/**
 * 45.4: buzón de prueba. El backend del e2e arranca con `EMAIL_OUTBOX_DIR`
 * (`playwright.config.ts`) y, con el proveedor `log`, guarda ahí cada correo
 * como JSON (`backend/app/services/email.py`, `_write_outbox`). En producción
 * no escribe nunca.
 */
export const OUTBOX_DIR = process.env.E2E_OUTBOX_DIR ?? join(tmpdir(), 'whetzy-e2e-outbox');

export interface SentEmail {
  to: string;
  subject: string;
  html: string;
}

/** Correos enviados a `to`, en el orden en que salieron. */
export function emailsTo(to: string): SentEmail[] {
  let names: string[];
  try {
    names = readdirSync(OUTBOX_DIR).filter((n) => n.endsWith('.json')).sort();
  } catch {
    return [];
  }
  return names
    .map((n) => JSON.parse(readFileSync(join(OUTBOX_DIR, n), 'utf-8')) as SentEmail)
    .filter((e) => e.to === to);
}

/** Ruta y query del enlace de verificación (el host del correo es el de producción). */
export function verifyPath(html: string): string {
  const m = html.match(/href="([^"]*\/verify-email\?[^"]*)"/);
  if (!m) throw new Error(`sin enlace de verificación en el correo:\n${html}`);
  const url = new URL(m[1].replace(/&amp;/g, '&'));
  return `${url.pathname}${url.search}`;
}
