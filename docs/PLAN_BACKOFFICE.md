# Plan — Back-office de soporte: usuarios, acciones y registro (serie 44)

> **Normativo-vivo.** Pedido del dueño del 2026-10-17. Va **después de la serie 43**
> (`PLAN_FLUJO_ALUMNO.md`) y antes de lo que quede de la 42. No toca contenido (ADR-62).
> Los números de serie (44) y de filas H (H.62, H.63) son provisionales: la sesión que lo
> incorpore los confirma con `grep -n '^### 4' docs/AUTONOMOUS_STATE.md | tail -1` y
> `grep -n '^| H\.' docs/AUTONOMOUS_STATE.md | tail -3`.

## 1. Por qué

El dueño solo ve a sus usuarios **en agregado**. Para ver a una persona concreta tendría
que abrir Postgres en Railway, sin control ni rastro. Con probadores reales hace falta
responder «no puedo entrar», «pagué y no tengo el plan» o «bórrame la cuenta» desde la
app, con el mínimo acceso necesario y dejando registro.

Estado en `master` 7446aa70, comprobado el 2026-10-17:

- Panel de administración en `AdminScreen.tsx` con 7 pestañas (`:182-189`). Desde el
  2026-10-15 es solo del rol `owner` (`admin.py:32-40`).
- 36 rutas `/admin/*`, todas de agregados (métricas, seguridad, contenido, ops, RGPD,
  ingresos, economía). **Ninguna busca un usuario ni actúa sobre él.**
- `AuditLog` (`models/auth.py:100`) registra eventos de seguridad (`security.py:718-733`),
  **no** las acciones del administrador.
- Primitivas que ya existen y se reutilizan:
  - `jwt_version` (`models/user.py:53`), para cerrar todas las sesiones;
  - `is_active` (`:48`), para suspender;
  - `granted_tier` y su caducidad (`:86-102`), para regalar plan temporal;
  - `POST /auth/resend-verification` (`auth.py:521`);
  - bloqueos (`/admin/security/lockouts`);
  - cola de borrado RGPD (`/admin/gdpr/deletions`);
  - `paddle_subscription_id` (`models/user.py:81`);
  - verificación en dos pasos: `User2FA` (`models/auth.py`) y `/auth/2fa/setup|enable|status` (`auth_hardening.py:124-197`).
- PostHog está aprobado (ADR-50) pero no hay SDK en el código (grep vacío). La analítica
  sigue bajo el veto de la fila 31.5 (nada nuevo hasta ≥ 100 usuarios).

## 2. Decisiones

| # | Decisión |
|---|---|
| B1 | Pestaña **«Usuarios»** dentro del panel existente, solo `owner` (`require_owner`). Sin aplicación aparte. |
| B2 | **Búsqueda** por email, usuario o prefijo de id; mínimo 3 caracteres; paginada (20). El listado muestra solo usuario, email enmascarado (`fe***@gmail.com`), alta y estado. |
| B3 | **Ficha**. Cuenta: alta, email verificado, idioma, activa o suspendida, rol, último acceso. Plan: `subscription_tier`, `granted_tier` y caducidad, compras de certificación, enlace al cliente en Paddle por `paddle_subscription_id`. Progreso en resumen: ruta activa, skills practicadas, banda de preparación. Seguridad: últimos eventos de `AuditLog` y bloqueos. RGPD: exportación o borrado pendiente. |
| B4 | **Cinco acciones**, cada una con **motivo obligatorio**: reenviar verificación; cerrar todas las sesiones (`jwt_version += 1`); desbloquear; regalar plan temporal (`granted_tier`, máximo 90 días); suspender o reactivar (`is_active`). El borrado de cuenta usa la cola RGPD que ya existe; no se crea otro camino. |
| B5 | **Prohibido**: ver o cambiar contraseñas, entrar como el usuario (impersonar), exportar listas de emails, editar el progreso o el dominio. |
| B6 | **Registro de administración**: tabla nueva `admin_action_log` (actor, usuario afectado, acción, motivo, datos JSON, fecha, IP), solo de añadir. Se registra **también abrir una ficha** (`view`). Pestaña «Registro» para leerlo. |
| B7 | El back-office exige que la cuenta del dueño tenga **verificación en dos pasos** activa; si no, responde 403 con el motivo. Paso previo del dueño: fila H.62. |
| B8 | **Analítica en agregado**: se queda en lo que ya da el panel. PostHog y similares esperan al umbral de la fila 31.5. **Tickets**: fuera de alcance; el canal sigue siendo el correo de soporte. La ficha ofrece «copiar email». |

## 3. Serie 44 (una rama y un PR por fila; test rojo→verde; suite entera; verificador §7)

| Fila | Qué | Ficheros clave | Tests (rojos hoy) |
|---|---|---|---|
| 44.1 (M) | `GET /admin/users?q=` y `GET /admin/users/{id}`; migración `admin_action_log`; registro de `view`; exige 2FA (B7) | `backend/app/api/v1/endpoints/admin.py`, `models/` (tabla nueva), migración Alembic, `tests/authz_matrix.json`, `docs/API.md` | no-owner → 403; owner sin 2FA → 403; búsqueda de 2 caracteres → 422; abrir ficha crea fila `view`; email enmascarado en el listado |
| 44.2 (M) | `POST /admin/users/{id}/actions/{accion}` para las cinco acciones de B4, cada una con motivo y fila en el registro | `admin.py`, `security.py` (reutilizar), `auth.py:521` | un test por acción (efecto + fila de registro); motivo vacío → 422; plan regalado de más de 90 días → 422; suspender invalida la sesión |
| 44.3 (M) | Pestañas «Usuarios» y «Registro» en `AdminScreen` (búsqueda, ficha, acciones con diálogo de motivo); i18n ES/EN | `frontend/src/pages/AdminScreen.tsx`, `services/api.ts`, i18n | vitest de búsqueda, ficha y acción; e2e `admin.spec.ts`: el dueño busca, abre una ficha y regala un plan; un alumno no ve la pestaña |
| 44.4 (S) | Docs: `MAPA_PRODUCTO.md`, `ARCHITECTURE.md`, `RUNBOOK.md` (cómo atender las peticiones típicas de soporte) | docs | `check_docs.py` verde |

Migración: `downgrade` probado y HEAD triple (CLAUDE.md, ledger, RUNBOOK) en el mismo PR
(SESIONES.md §5). Sin cambios en `content/**`.

## 4. Filas H (dueño)

- **H.62** (hecha el 2026-10-17: el dueño la activó, «Two-step verification is on», 10 códigos de respaldo): verificación en dos pasos en la cuenta del dueño antes de desplegar 44.1.
- **H.63** (resuelta el 2026-10-17 en el mismo PR que este plan, aprobada por el dueño al fusionarlo): la política publicada dice para qué abre el titular una cuenta (`legal.privacySupportAccess`, ES/EN, en `LegalScreen.tsx`). La fila 44.4 le añade «y queda registrado» cuando el registro de administración esté en producción; antes no sería verdad.

## 5. Verificación de extremo a extremo

- `bash scripts/ci_local.sh` entero y `npx playwright test` sin rojos.
- Tras la fusión: con la cuenta del dueño (2FA activa), buscar un usuario de prueba, abrir
  su ficha, regalarle Pro 7 días con motivo, y ver las dos filas (`view` y `grant_plan`) en
  «Registro». Con una cuenta de alumno, `/api/v1/admin/users?q=abc` → 403.
- `alembic heads` con un solo HEAD, igual a las tres líneas documentadas.
