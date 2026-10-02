# Mapa del producto — páginas, pantallas, subvistas y dónde se especifican

Inventario único de **todo lo que existe en la app** y del documento que lo especifica.
Hasta el 2026-10-01 ningún documento enumeraba todas las pantallas (el que más nombraba
era el ledger, 15 de 31); este fichero cierra ese hueco. La fuente de verdad es el código:
`frontend/src/App.tsx` (rutas y conmutador), `frontend/src/stores/useAppStore.ts` (tipo
`Screen`) y `frontend/src/pages/`. La guarda `scripts/check_docs.py` comprueba que cada
fichero de `frontend/src/pages/` y cada ruta de `App.tsx` aparecen aquí: si añades una
pantalla sin apuntarla, el commit no pasa.

Nivel de especificación de la columna «Especificación»:
**E2** = qué muestra, cómo se comporta, estados y criterio de aceptación;
**E1** = qué es y para qué, sin detalle para construirla;
**E0** = solo mencionada (ledger, STATUS, competencia).

## 1. Rutas con URL propia (fuera de la sesión)

Se resuelven en `App()` antes de cualquier hook; no necesitan sesión salvo donde se dice.

| Ruta | Pantalla | Para qué | Especificación |
|---|---|---|---|
| `/landing` | `LandingScreen` | Portada pública, ES/EN, hero pre-renderizado | E1: `docs/design/identidad.md`, `competitive-teardown.md` |
| `/auth`, `/login`, `/register` | `AuthScreen` (modos login / register / forgot → `ForgotPasswordPage`) | Acceso, registro, recuperar contraseña, OAuth GitHub/Google, segundo paso con código si la cuenta tiene 2FA (O1.3) | E1: `docs/design/auth-hardening.md`, `docs/API.md` |
| `/reset-password?token=` | `ResetPasswordPage` | Nueva contraseña desde el correo | E0: `docs/API.md` (endpoint) |
| `/delete-account` | `DeleteAccountScreen` | Borrado de cuenta (GDPR, purga a 30 días) | E1: política publicada (`legal.privacy*`, ADR-55), `RUNBOOK.md` |
| `/privacy`, `/terms`, `/refund` | `LegalScreen doc=…` | Textos legales publicados (claves i18n `legal.*`) | E1: las propias claves `legal.*` (ADR-55; los borradores, en `docs/archive/legal-borradores/`) |
| `/evidence` | `EvidenceScreen` | Cifras reales del producto | E0: ledger 38.5 |
| `/status` | `StatusPage` | Estado público del servicio | E0: ledger 22.7 |
| `/checkout?plan=&track=` | `CheckoutScreen` | Pago web con Paddle (cabeceras propias, sin COEP) | E1: ledger H.29, `docs/API.md` |
| `/admin` | `AdminScreen` (7 pestañas: metrics, security, content, ops, gdpr, revenue, economy) | Panel del dueño (`role=owner`) | E2: `docs/design/admin-spec.md` |
| `/certificate/<código>`, `/verify/<código>` | `CertificateScreen` | Verificación pública de un certificado | E1: `docs/ECONOMIA.md` §11, ADR-37 |
| `/u/<usuario>` | `PublicProfileScreen` | Perfil público opt-in | E0: `SEGMENTOS.md`, `ECONOMIA.md` |
| `/r/<código>` | (redirección) | Guarda el código de referido y lleva a `/register` | E1: `docs/ECONOMIA.md` §3 |
| `/` | la app con sesión (§2) | — | — |
| `/_ui` | `UiKitScreen` | Muestrario de componentes, **solo en desarrollo** (`import.meta.env.DEV`) | — (herramienta interna) |

## 2. Pantallas dentro de la app (tipo `Screen`, sin URL)

Navegación inferior de 5 pestañas (design/v2): **Hoy · Rutas · Practicar · Ranking · Yo**.
Antes de Hoy, un usuario nuevo pasa por `OnboardingScreen` (una vez por usuario).

| `Screen` | Pantalla | Se llega desde | Subvistas | Especificación |
|---|---|---|---|---|
| `home` | `HomeScreen` | pestaña Hoy | preparación, siguiente paso, repaso FSRS, racha, tus rutas, misiones, territorio, herramientas | E2: `design/v2/brief-msg1.md` |
| `tracks` | `TracksScreen` | pestaña Rutas, filas de «Tus rutas» | catálogo (filtros Todas / Aprender / Certificaciones) y detalle (vistas Currículo / Mapa / Glosario; en cada módulo disponible, la prueba para saltarlo si el backend puede montarla, O1.4) | E2: `design/v2/brief-msg2.md` §A–B |
| `lesson` | `LessonScreen` | «Aprender», una habilidad en Rutas | pasos de texto + paso de ejemplo | E2: `design/v2/brief-msg2.md` §C |
| `quiz` | `QuizScreen` | pestaña Practicar, «Practicar», repaso | pregunta, ejecución de código, feedback, tutor («¿Por qué?», con etiqueta de IA y «Reportar esta explicación»; se apaga en Ajustes), «Reportar un problema» con la pregunta | E2: `design/v2/brief-msg2.md` §D |
| `placement` | `PlacementScreen` | «¿Ya sabes algo de esto?» en el detalle de ruta | intro, cargando, test, resultado, error | E0: ledger |
| `readiness` | `ReadinessScreen` | «Preparación para la certificación» | arco + barras por dominio | E2: `design/v2/brief-msg2.md` §E |
| `mockexam` | `MockExamScreen` | «Simulacro de examen» | modos simulacro / certificador; fases intro, en curso, corrigiendo, resultado | E2: `design/v2/brief-msg2.md` §F |
| `trackexam` | `TrackExamScreen` | «Examen final del curso» | intro, examen, resultado; admite `test_out` de módulo, pero nada en la UI lo lanza (§5.1) | E2: `design/v2/brief-msg2.md` §F |
| `league` | `LeagueScreen` | pestaña Ranking | pestañas Liga / Duelos (`RankingTabs`) | E1: `docs/API.md` (league) |
| `duels` | `DuelScreen` | pestaña Ranking → Duelos | lista (nombre de la habilidad, no su id), reto (rival + habilidad practicada o al azar entre las practicadas), jugando, resultado. Un duelo no da XP | E0: ledger 3.1 |
| `profile` | `ProfileScreen` | pestaña Yo | ajustes (incluida la verificación en dos pasos: alta con QR, desactivar con código), plan y cancelación, plan ganado con referidos y hasta cuándo (ADR-57), tema, idioma, accesos a Stats/Cartera/Instructor/Admin | E1: `design/v2/brief-msg1.md` (nav) |
| `stats` | `StatsScreen` | Yo → Estadísticas | resumen y progreso | E0: ledger |
| `wallet` | `WalletScreen` | Yo → Cartera | saldo, fuentes y gastos que lista `/economy/prices`, canje de códigos; «Invitar amigos» solo si el referido figura como fuente (desde ADR-57, sí). Sin lista de movimientos | E1: `docs/ECONOMIA.md` §2–5 |
| `instructor` | `InstructorScreen` | Yo → Instructor | panel del instructor | E1: `docs/MARKETPLACE.md` §4 |
| `marketplace` | `MarketplaceScreen` | Yo → Marketplace; deslizar a la izquierda en móvil | catálogo con filtros Todos / Aprender / Certificación | E1: `docs/MARKETPLACE.md` |
| `playground` | `PlaygroundScreen` | Hoy → Herramientas | editor Python / SQL / JS | E0: CHANGELOG (serie 19) |
| `projects` | `ProjectScreen` | Hoy → Herramientas | proyecto multi-paso, pasa / falla | E0: CHANGELOG |
| `admin` | `AdminScreen` | Yo → Admin (solo owner) | las 7 pestañas de `/admin` | E2: `docs/design/admin-spec.md` |

Total: **14 rutas URL en producción** (más `/_ui` en desarrollo y la redirección `/r/`),
**18 pantallas** del tipo `Screen` más el onboarding, **31 ficheros** en `frontend/src/pages/`.

## 3. API

149 operaciones en `backend/app/api` (148 vivas en el OpenAPI local del 2026-10-01 + `POST
/billing/paddle/cancel`, que llegó con el #64). `docs/API.md` documenta todas salvo `GET /`
(la raíz). Comprobación: comparar `/api/v1/openapi.json` con los `MÉTODO /ruta` de API.md.

## 4. Contenido

Cifras con `python scripts/catalog_coverage.py` (no se copian aquí para que no envejezcan).
El 2026-10-01: 45 rutas en el plan, 24 construidas, 2 en cuarentena, 19 planificadas; 0 en la
forma de ADR-54. Pendiente en las construidas: 261 habilidades, 261 lecciones, 266 términos y
2.610 preguntas.

## 5. Huecos

### 5.1 Prometido en un documento y sin código (comprobado el 2026-10-01)

Búsqueda en `frontend/src` y `backend/app` (sin tests) y en las claves i18n ES.

| Qué | Dónde se promete | Estado del código |
|---|---|---|
| Panel B2B / equipos | `docs/legal/b2b_pilot_offer_*.md`, ledger 24.9 | no existe |
| `/blog`, `/compare`, `/pricing` | ledger 26.9, 27.10; `archive/SPEC_WEB.md` | no existen |
| Sign in with Apple | ADR-13 (obligatorio antes de App Store) | no existe (bloqueado por H.2) |
| Comunidad y grupos de estudio | ledger 40.7–40.8 | no existe |
| Widgets interactivos, tutor por voz | ledger 40.1–40.6 | no existe |
| Vídeos | ledger 18.9 | no existe |
| Créditos por proyecto entregado (200) y por simulacro aprobado (150) | `docs/ECONOMIA.md` §2.2 | **no se pagan**: el paso de proyecto lo da por bueno el navegador (`passed` del cliente) y el simulacro no tiene nota de corte. Los demás grifos de aprendizaje sí (`services/learning_rewards.py`, 2026-10-02) |
| Antifraude por dispositivo/IP (1 activación cada 30 días) | `docs/ECONOMIA.md` §3.5 | el código existe (`check_device_rate_limit`), pero el frontend no manda `X-Device-Fingerprint` y la política publicada no declara ese tratamiento: no corre (ADR-57) |
| IP y navegador de los inicios de sesión en la política de privacidad | RGPD art. 13; `legal.privacyL1`–`L5` (ADR-55) | se guardan en claro (`login_attempts`, `user_sessions`, `audit_log`) sin retención por tiempo y la política publicada no los nombra; texto propuesto en `docs/legal/antifraud-legal-basis.md` §«Para publicar», pendiente del dueño |
| Clawback de referidos automático (reembolso, baneo) | `docs/ECONOMIA.md` §3.5 | el clawback existe como acción de admin (Admin → Economía → Referidos, 2026-10-02); **nada lo dispara solo**: no hay flujo de baneo, y un reembolso del referido no está ligado a su activación |
| Gastar créditos en simulacro, informe PDF o curso | `docs/ECONOMIA.md` §2.3 | `spend_fifo` solo lo llama el comodín de racha (`services/streak_shop.py`) |

### 5.2 Existe y no tiene especificación (E0 en §1–§2)

`ResetPasswordPage`, `EvidenceScreen`, `StatusPage`, `PublicProfileScreen`, `PlacementScreen`,
`DuelScreen`, `StatsScreen`, `PlaygroundScreen`, `ProjectScreen`: solo menciones. Si una de
ellas se rehace, su especificación se escribe aquí o en un brief antes de tocar el código.

### 5.3 Contradicciones comprobadas

- Reparto del marketplace: **70 %** en `docs/legal/instructor_recruitment_kit_en.md:19` y
  `docs/MARKETPLACE.md:22`; **80 %** en `MARKETPLACE.md:41` y en el borrador archivado
  `docs/archive/legal-borradores/raiz-terms-of-service.md:61`
  (ADR-41). Manda ADR-41 (80 %); el kit y la línea 22 están desfasados. `docs/API.md:260`
  dice «Reparto 70/30»: también desfasado.
