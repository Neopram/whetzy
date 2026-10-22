# Capturas: páginas legales pre-renderizadas

Evidencia del PR que pre-renderiza `/terms`, `/privacy` y `/refund` (2026-10-21). La revisión del
dominio de Paddle pide los Términos, los Reembolsos y la Privacidad accesibles. Hasta este PR, las tres
rutas llegaban como el shell vacío de la SPA: 3.289 B sin texto, comprobado ese día en producción con
`curl`.

Capturadas el 2026-10-21 con Playwright (Chromium) contra `vite preview` del build de producción
(`npx vite build`), a 390 px salvo las indicadas:

- `terms-sinjs-390.png`, `privacy-sinjs-390.png`, `refund-sinjs-390.png`: el HTML tal como llega, con los
  scripts de la app bloqueados. Sale el texto completo en español y con el estilo de la página.
- `terms-sinjs-1280.png`: lo mismo a 1280 px, con JavaScript desactivado.
- `terms-js-390.png`, `terms-js-1280.png`: con la app cargada. El texto pasa al idioma del navegador
  (inglés en Playwright), igual que la landing.

axe (WCAG 2.2 AA): 0 violaciones en las tres páginas, con la app y sin ella. Antes de este PR marcaba
`landmark-one-main` y `region`, porque `LegalScreen` no tenía `<main>`.
