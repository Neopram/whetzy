# Capturas: contraste del editor de código

Evidencia del PR del tema propio del editor (`frontend/src/lib/monacoTheme.ts`).
Captura del 2026-10-20 con Playwright (Chromium) contra el stack local (Postgres 16 +
Redis, backend en `:8000`, Vite en `:5199`), con el proyecto SQL que siembra
`backend/scripts/seed_e2e_project.py` y una cuenta registrada de cero. La genera
`frontend/e2e/editor-contraste.spec.ts`.

- `editor-sql-es-390.png`: el paso 1 del proyecto con un comentario, palabras clave,
  un número y la cadena `'Rex'`. Cada fragmento coloreado mide ≥ 4,5:1 sobre el fondo
  del editor (`#1E1E1E`), medido en el navegador con `getComputedStyle`.

Con el tema anterior (`vs-dark`) el mismo spec sale en rojo: los comentarios a 4,21:1 y
la cadena `'Rex'` a 4,17:1 (rojo puro, `#FF0000`).

axe (WCAG 2.2 AA) sin excluir `.monaco-editor`: 0 violaciones.
