# Capturas — 46.15 D, movimiento en las pantallas de progreso

Evidencia del PR de la fila 46.15, bloque D (`docs/PLAN_UI_AVANZADA.md` §7.5).

**Cómo se hicieron**
- **Fecha y entorno:** 2026-10-20, Playwright (Chromium) contra el backend local real.
- **Spec:** `frontend/e2e/progreso.spec.ts` (4 casos).
- **axe (WCAG 2.2 AA):** 0 violaciones en todas las capturas.

**Capturas**
- **`perfil-insignia-nueva-es-390.png`:** las insignias entran escalonadas y la ganada desde la última visita brilla una vez (borde de marca y destello).
  - La foto es propia de Perfil, como la de Hoy y la de Rutas.
  - Sin foto previa no brilla nada.
  - **Dato añadido:** una cuenta nueva no gana ninguna insignia con un quiz (la más fácil, `perfectionist`, pide una sesión perfecta). Se añade esa insignia, tal cual está en el seed, a la respuesta de `/badges`.
- **`estadisticas-es-390.png`:** la barra de la ruta crece desde 0 y las dos listas entran escalonadas.
  - **Dato añadido:** sin skills dominadas no hay barra, así que se sube `skills_mastered` en la respuesta de `/progress/dashboard`.
  - El «Elo» de la lista solo sale en desarrollo (`import.meta.env.DEV`, ADR-60).
- **`cartera-es-390.png`:** las listas de ganar y gastar créditos entran escalonadas.
- **`certificado-es-{390,1280}.png`:** verificación pública de un certificado válido; el sello se dibuja.
  - Revocado no hay sello (e2e y vitest).
  - **Dato añadido:** sin un examen final aprobado en local no existe un código válido, así que se responde a la verificación.
  - El QR sale roto **por eso mismo**: lo sirve el backend (`/exams/certificates/<code>/qr`) y ese código no existe en la base local.

**Lo que el plan pedía y no se hace**
- **Contar cifras con `CountUp`** (Estadísticas, saldo de la Cartera): el componente vive en #273 (46.7b), aún sin fusionar. Queda para después.
- **Informe de dominio y perfil público:** no muestran bandas, sino listas de rutas, certificados y proyectos. Lo que entra escalonado son esas listas (vitest; el perfil público está detrás de `PUBLIC_PROFILES_ENABLED=False` y el informe se compra con créditos).

**Hallazgo aparte (no es de este PR)**
- La verificación pública del certificado sale **siempre en español** para un visitante sin cuenta, aunque su navegador esté en inglés: `StandaloneCertificate` (`App.tsx`) aplica el `user.language` del store, que vale `'es'` por defecto.
- Por eso aquí no hay captura «EN».
- Propuesto como tarea aparte.
