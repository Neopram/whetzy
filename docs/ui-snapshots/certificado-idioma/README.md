# Capturas — certificado público en el idioma del visitante

**Fallo:** la verificación pública del certificado (`/certificate/<código>`) salía siempre en español a un visitante sin cuenta, aunque su navegador estuviera en inglés.
- **Causa:** la página aplicaba `user.language` del store, que para quien no ha entrado nunca es el `'es'` por defecto.
- **Mismo fallo en:** el informe público (`/report/<código>`) y las páginas legales.

**Arreglo** (`frontend/src/lib/standaloneLanguage.ts`), por orden:
1. `?lang=` manda.
2. Con cuenta, el idioma de la cuenta.
3. Sin cuenta, lo elegido en la portada (`whetzy_lang`) o el idioma del navegador.

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium), sin sesión.
- **Spec:** `frontend/e2e/certificado-idioma.spec.ts` (4 casos, axe 0).
- **Datos:** se intercepta la respuesta de verificación, porque en local no existe un certificado válido. Por eso el QR sale roto.
- **Visto en rojo con el `App.tsx` de `master`:** salió «Comprobación de certificado» y `lang="es"` con el navegador en inglés.

**Capturas**
- **`certificado-en-390.png`:** navegador en inglés.
- **`certificado-es-390.png`:** navegador en español.
