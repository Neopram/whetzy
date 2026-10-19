# Capturas — 46.3a, estados vacío, de carga y de error con los tokens `--le-*`

Evidencia del PR de la fila 46.3a (`docs/PLAN_UI_AVANZADA.md` §2). Capturas del
2026-10-18 de la página de componentes `/_ui` (solo en desarrollo), a 390 px, con
Playwright (Chromium) contra dos servidores Vite: `master` (`antes`) y esta rama
(`despues`). El tema se fija con `whetzy_theme` antes de cargar.

- `estados-{dark,light}-{antes,despues}.png`: Skeleton, EmptyState y el inicio de
  LoadingState. Sin cambio visible: cada token viejo se cambió por el `--le-*` de
  mismo valor en los dos temas (tabla en el PR).
- `reintentar-hover-{dark,light}-{antes,despues}.png`: el botón «Reintentar» de
  ErrorState con el ratón encima. **Antes**, el texto era `--bg-light`, que no
  cambia con el tema: `rgb(245, 247, 251)` también en modo claro, casi blanco
  sobre la tinta roja clara. **Después**, `--le-text`: `rgb(232, 236, 241)` en
  oscuro y `rgb(26, 26, 46)` en claro (valores leídos con `getComputedStyle`).
