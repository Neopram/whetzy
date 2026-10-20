# Capturas — 44.3, pestaña «Usuarios» del panel de administración

Evidencia del PR de la fila 44.3 (`docs/PLAN_BACKOFFICE.md` B2–B4). Capturas del
2026-10-20 con Playwright (Chromium) contra el stack local (Postgres 16 + Redis,
backend en `:8000`, Vite en `:5199`), hechas por `frontend/e2e/admin.spec.ts`.

Las rutas `/admin/users*` están **simuladas** en ese test: un e2e no puede darse
rol de dueño ni 2FA sin tocar la base. Los datos (`anabanana`,
`federica@gmail.com`) son inventados. Lo que hace el servidor lo prueban los
tests de integración de 44.1 y 44.2 contra Postgres.

- `ficha-es-{390,1280}.png`: la ficha tras buscar «fede» y abrir el resultado.
  En la lista el email va enmascarado (`fe***@gmail.com`); en la ficha va
  entero, con «Copiar email». A 390 px cada etiqueta va encima de su valor.
- `regalar-plan-es-{390,1280}.png`: el diálogo de «Regalar plan», con plan,
  días (1–90) y motivo obligatorio. «Confirmar» está apagado hasta que hay motivo.

axe (WCAG 2.2 AA) sobre la ficha: 0 violaciones, en los dos anchos. Sin
desbordamiento horizontal a 390 px.
