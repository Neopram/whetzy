# Capturas: /auth, ola 2 (Apple y Google arriba, con su estilo de marca)

Evidencia del PR de la pantalla de entrada de la ola 2 (2026-10-21).

**Cómo se capturaron.** Playwright (Chromium) contra `vite` en local, el 2026-10-21. `antes-*` es
`master` (`4389cde`) y `despues-*` es esta rama. `/auth/oauth/providers` está simulado con
`["apple", "google"]`: en producción hoy solo sale Google, porque Apple espera sus credenciales
(H.2). El tema se fija con `whetzy_theme` en el almacenamiento local, que es lo que lee la app;
la preferencia del sistema no cuenta.

Combinaciones: crear cuenta e iniciar sesión, en oscuro y en claro, a 390 px. A 1280 px, solo
el oscuro.

**Lo que cambia en `despues-*`:**
- **Orden.** Apple y Google van antes del formulario, con el separador «o con tu correo».
  Antes quedaban debajo de «Empezar a aprender», fuera de la primera pantalla al crear cuenta a
  390 px.
- **Colores de marca**, como tokens `--le-oauth-*` en los dos temas:
  - Google, con las variantes «dark» y «light» de su guía de marca;
  - Apple, blanco sobre el tema oscuro y negro sobre el claro.

  Los valores salen de las guías de marca de Google y de Apple tal como se conocían al escribir
  esto; no se volvieron a descargar en esta sesión.
- **Enlaces legales.** «Términos» y «Política de privacidad» son enlaces a `/terms` y `/privacy`;
  antes eran texto plano.
- **Tuteo.** «¿Olvidaste tu contraseña?» (antes «¿Olvidó su contraseña?», lo único en usted de la
  pantalla).

**axe (WCAG 2.2 AA):** 0 violaciones en las 16 combinaciones (antes y después; crear cuenta e
iniciar sesión; oscuro y claro; 390 y 1280 px). Sin scroll horizontal en ninguna.
