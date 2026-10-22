# Capturas: catálogo por campos (ola 2)

Evidencia del PR del catálogo por campos (2026-10-21). El dueño eligió los cinco campos de la
maqueta, que son los mismos grupos que ya usa el onboarding (`lib/trackGroups.ts`):
Programación, Desarrollo de software, Datos e IA, Cloud e infraestructura, y Seguridad y redes.
Las 11 certificaciones tienen el suyo en `CERT_FIELDS`. `content/**` no se toca (ADR-62).

**Cómo se capturaron.** `e2e/catalogo-campos.spec.ts`, Playwright (Chromium) contra `vite` y el
backend local con el contenido de verdad (35 rutas), el 2026-10-21, en ES a 390 y a 1280 px:

- `todos-*`: el catálogo sin filtrar;
- `seguridad-*`: el campo «Seguridad y redes»;
- `seguridad-certificaciones-*`: ese campo y el tipo «Certificaciones».

**Lo que comprueba la misma prueba:**
- axe (WCAG 2.2 AA): 0 violaciones en cada paso;
- el campo reduce la lista y el tipo la reduce más;
- con «Certificaciones», «Desarrollo de software» desaparece porque no tiene ninguna.

En `seguridad-es-1280.png` los recuentos por campo son 7, 6, 10, 8 y 4, y suman las 35 rutas de
«Todos los campos».
