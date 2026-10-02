# Whetzy — Economía cerrada: créditos, referidos, códigos, rails y credenciales

> **Documento vivo nº 16.** Manda sobre cualquier mención de créditos, recompensas,
> referidos, códigos promocionales, pagos en stablecoin, certificados verificables
> o «token» en otros documentos. Última actualización: 2026-09-18 (sesión bh).
> ADRs que lo sostienen: **ADR-33** (no hay token), **ADR-34** (créditos),
> **ADR-35** (referidos y códigos), **ADR-36** (USDC como rail), **ADR-37**
> (credenciales verificables), **ADR-38** (track32 Solana/Web3). Implementa la
> **Serie 29** de `AUTONOMOUS_STATE.md`.
> Regla de este documento: **coste cero** (ADR-15) y **cero exposición regulatoria**.

---

## 0. Por qué existe este documento

El dueño propuso el 2026-09-18 integrar una criptomoneda propia en Solana como
recompensa, inversión (staking) y herramienta de retención. La evaluación honesta
(ADR-33) concluyó que el **token** destruye lo que Whetzy tiene de único (el motor,
que se envenena con datos de bots), la saca de las tiendas (Apple 3.1.5), la mete
en MiCA/Howey, cuesta dinero real (liquidez, legal, auditoría) y espanta a cualquier
adquirente edtech. Pero **los cinco instintos detrás de la idea eran correctos** y
cada uno tiene una versión que funciona sin nada de lo anterior:

| Instinto del dueño | Versión que funciona | ADR | Serie |
|---|---|---|---|
| «Una recompensa que retenga» | **Créditos Whetzy**: economía cerrada, sin valor externo | ADR-34 | 29.0–29.2, 24.6 |
| «Que crezca sola» | **Referidos por activación + códigos autogenerados** | ADR-35 | 29.3–29.7 |
| «Solana para pagos» | **USDC como rail** (Stripe *Pay with Crypto*; payouts a instructores) | ADR-36 | 29.9, 21.2, 28.7 |
| «Que exista on-chain» | **Credenciales verificables** Open Badges 3.0; cNFT opcional | ADR-37 | 29.10, 24.7 |
| «Solana está despertando» | **track32 Solana/Web3 en español** + Superteam como canal y financiación no dilutiva | ADR-38 | 37.8 (nivel C, ADR-53), 26.8, 27.9 |

Todo lo demás que prometía el token —«100 casos de uso», valoración, staking— no
sobrevive a la evidencia (§12).

---

## 1. La línea legal — tres reglas que lo mantienen a coste cero

Los créditos son una **moneda promocional cerrada**, como las gemas de Duolingo o de
Boot.dev. Siguen siéndolo mientras el código y los ToS cumplan **las tres reglas**:

| # | Regla | Qué pasa si se rompe |
|---|---|---|
| 1 | Los créditos **no tienen valor monetario ni se canjean por dinero**, ni por nada convertible en dinero fuera de Whetzy | Pasan a ser dinero electrónico (EMD2/PSD2 en la UE) o un valor mobiliario |
| 2 | **No se transfieren entre usuarios**, ni se regalan, ni se venden | Ídem: aparece un mercado secundario y con él la obligación de licencia |
| 3 | **No se compran con dinero**. Solo se ganan | En iOS, Apple 3.1.1 obligaría a IAP; en la UE se convierte en prepago |

Consecuencias operativas:

- **Canje de códigos y consulta de saldo: solo en web (`whetzy.com`).** Las apps
  iOS/Android muestran el saldo y las recompensas ya aplicadas, pero **no tienen
  campo de canje** (Apple 3.1.1: «license keys, QR codes» como mecanismo propio de
  desbloqueo). Las recompensas de la escalera (§3.3) se aplican **en el servidor**
  como *entitlements*; la app solo refleja el estado (Apple 3.1.3(b), multiplataforma).
- **Los créditos compran consumibles que Whetzy no vende por IAP** (simulacros,
  congelar racha, bootcamps async). Nunca compran suscripción por goteo (§2.3).
- **Caducan** a los 90 días sin uso (§2.4). Un saldo eterno es un pasivo contable y no retiene.
- Cláusulas literales para ToS/privacidad: tarea **29.11** → entran en **21.7**.
- Nada de esto requiere abogado antes de existir: es la misma figura que usan
  Duolingo, Boot.dev y DataCamp (XP/gemas). La revisión profesional (H.20) las
  leerá junto con el resto.

---

## 2. Créditos Whetzy — el modelo

### 2.1 Principio: sumidero > grifo

La economía se diseña **desde los sumideros** (en qué se gastan) y solo después se
abren los grifos (cómo se ganan). Si se hace al revés, se inflan y dejan de valer.
Valor nominal interno para modelar coste (nunca visible al usuario): **1 crédito ≈ $0,01**.

### 2.2 Grifos — cómo se ganan

| Evento | Créditos | Tope | Segmento que más lo usa |
|---|---|---|---|
| Diagnóstico inicial completado | 50 | 1 vez | Todos |
| Módulo completado (BKT ≥ 0,8 en todas sus skills) | 100 | por módulo | Estudiante |
| Racha de 7 días | 70 | por semana | Estudiante |
| Racha de 30 días | 300 | por mes | Estudiante, Career-switcher |
| Proyecto multi-paso entregado con tests verdes | 200 | por proyecto | Career-switcher |
| Skill saltada con BKT confirmado (test-out) | 50 | por skill, máx. 500/mes | Developer Senior |
| Simulacro de certificación aprobado (≥ corte) | 150 | por cert y nivel | Career-switcher |
| **Referido activado** (§3) | **300** | 10 activaciones/mes | Todos |
| **Bienvenida como referido** (§3) | **200** | 1 vez | Todos |
| Código de campaña (§4) | 100–200 según campaña | 1 por código | Todos |
| Código de reactivación (§4) | 200 (caduca en 72 h) | 1 cada 60 días | Inactivos |
| Empleado de empresa: módulo asignado completado | 100 → **bolsa de la empresa** | por módulo | Empresa |

**Tope global de ganancia por aprendizaje: 1.500 créditos/mes** (los referidos
tienen su propio tope).

**Estado en el código (2026-10-02, `services/learning_rewards.py`).** Se pagan el
diagnóstico, el módulo (todas sus skills ≥ 0,8), la skill saltada con un test-out
aprobado a tiempo (≥ 0,8 tras la prueba, tope 500/mes), y las rachas de 7 días
(una vez por semana ISO mientras dure) y de 30 (una vez al mes). Se abonan al
cerrar una sesión (`/quiz/end`), al enviar un examen de ruta o test-out y en la
vuelta horaria de `periodic_jobs_loop`. Lo que no cabe en el tope no se paga a
medias: un módulo o una skill se pagan el mes siguiente; la racha de un periodo
pasado no vuelve. **No se pagan** el proyecto (el «tests verdes» lo afirma el
navegador) ni el simulacro aprobado (el simulacro no tiene nota de corte), ni el
del empleado de empresa (no hay panel B2B). Con el tope, el máximo que un usuario Free puede extraer al
mes son tres simulacros: suficiente para retener, insuficiente para vivir de ello.

### 2.3 Sumideros — en qué se gastan

| Consumible | Precio | Nota |
|---|---|---|
| Simulacro de certificación (formato real) | 500 | Lo que más quiere el estudiante y no puede pagar |
| Congelar racha (1 día) | 150 | Duolingo lo vende; aquí se gana |
| Informe de dominio en PDF | 300 | Compartible con empleadores. **En el código (2026-10-02):** instantánea pública en `/report/<código>` (128 bits, como un certificado) con «Guardar como PDF» por la impresión del navegador; sin dependencia de PDF en el servidor |
| Bootcamp async (1 secuencia) | 3.000 | Solo Career-switcher/Senior lo alcanzan |
| Curso del marketplace (instructor) | según instructor, mínimo 1.000 | El 80 % del instructor (ADR-41) se liquida al valor nominal (§2.1) desde la bolsa de marketing de Whetzy, nunca del alumno |
| Seat extra 1 mes (solo empresa, desde la bolsa de empresa) | 2.000 | Retención B2B |

**Lo que los créditos NO compran:** meses de Pro/Pro Max (eso es premio de escalera,
§3.3, no de goteo), certificaciones oficiales de terceros (dinero real del proveedor),
nada fuera de la app.

### 2.4 Caducidad y contabilidad

- Cada abono es un **lote** con `expires_at = created_at + 90 días`. El gasto
  consume lotes **FIFO** (el que antes caduca, primero).
- Un job diario (cola de trabajos de 22.6) escribe un asiento negativo `expire`
  por cada lote vencido. Nunca se borra nada.
- El saldo **es la suma del ledger**, no una columna. No existe `users.credits`.
- Aviso 7 días antes de una caducidad ≥ 200 créditos (email ES/EN nativo): es la
  palanca de retención más barata del sistema.
- **Estado en el código (2026-10-02):** las dos cosas corren en la vuelta horaria
  de `periodic_jobs_loop` (`services/periodic.py`). El asiento `expire` cierra lo
  que **quedaba** del lote y hereda su caducidad, como los gastos: el saldo no se
  mueve al escribirlo (la versión anterior, sin llamar desde ningún sitio, habría
  restado el importe original para siempre). El aviso va una vez por fecha
  (`users.credit_expiry_warned_for`), solo a emails verificados y sin baja, con
  enlace de baja de un clic.

### 2.5 Ledger — esquema (29.0)

```sql
credit_ledger (
  id              bigserial primary key,
  user_id         uuid not null references users(id),
  amount          integer not null,             -- con signo; nunca 0
  reason          text not null,                -- enum: module_done, streak_7, streak_30, project,
                                                --  skip_confirmed, mock_passed, referral_activated,
                                                --  referral_welcome, promo_code, reactivation,
                                                --  spend_mock, spend_freeze, spend_report,
                                                --  spend_bootcamp, spend_marketplace, expire,
                                                --  clawback, admin_adjust
  ref_type        text,                         -- module | referral | promo_code | purchase | lot
  ref_id          text,
  lot_id          bigint references credit_ledger(id),   -- para gastos/caducidad: lote consumido
  idempotency_key text not null unique,         -- p. ej. "module_done:<user>:<module>"
  expires_at      timestamptz,                  -- solo en abonos
  created_at      timestamptz not null default now()
);
create index on credit_ledger (user_id, created_at);
```

Invariantes que los tests de 29.1 comprueban: la misma `idempotency_key` no abona
dos veces; el saldo nunca es negativo; un gasto referencia lotes vivos; `expire`
solo se aplica a lotes con `expires_at < now()` y saldo restante > 0; `clawback`
solo por reembolso, baneo o fraude confirmado (§3.5).

---

## 3. Programa de referidos

> **Estado (2026-10-01, ADR-57):** cableado en `services/economy.py`
> (`referral_program_loop`, cada 6 h). Cómo se leen el diagnóstico, el primer módulo y la
> racha, y qué falta (dispositivo/IP sin declarar en la política, clawback sin disparador):
> ADR-57.

### 3.1 La regla que decide si funciona

**Se paga por activación, nunca por registro.** Un registro cuesta 10 segundos y un
script; una activación exige a una persona real.

**Activación** = el referido (a) verifica el email, (b) completa el diagnóstico,
(c) termina su primer módulo y (d) mantiene una racha de 3 días. Se acredita **7 días
después** de cumplirse (d) si no hay marca de fraude. En ese punto el referido ya
está retenido: la recompensa premia lo que de verdad importa.

### 3.2 Doble cara

| Quién | Cuándo | Qué recibe |
|---|---|---|
| Referido | Al registrarse con código válido | 200 créditos de bienvenida (caducan en 30 días si no completa el diagnóstico) |
| Referente | Al activarse el referido (+7 días) | 300 créditos |

### 3.3 Escalera (lo que retiene al referente)

| Activaciones acumuladas | Premio | Cómo se aplica |
|---|---|---|
| 1 | 300 créditos | ledger |
| 3 | **1 mes de Pro** | entitlement en servidor; visible en todas las plataformas |
| 10 | **Una certificación oficial** (PCEP, CLF-C02 o ISC2 CC; voucher a cargo de Whetzy) | HUMAN-BLOCKED por importe (ADR-15) hasta que exista ingreso; mientras tanto: 6 meses de Pro Max |
| 25 | Badge «Embajador» + fila en el perfil público + acceso anticipado | perfil (24.8) |

Tope: **10 activaciones acreditables por mes**. La escalera es acumulativa y no caduca.

### 3.4 Mecánica

- Cada usuario tiene **un código permanente** (`referral_codes`), formato `NOMBRE-XXXX`
  (alfabeto seguro §4.3), y un enlace `whetzy.com/r/<código>` que fija el idioma del
  referente (ADR-17: el referido aterriza en `/es` o `/en`, nunca en una mezcla).
- El código se muestra en: fin de módulo, pantalla de racha, perfil, email semanal.
  Nunca en el primer minuto (primero valor, después petición).
- El código se aplica en registro o hasta 7 días después (campo en ajustes web).

### 3.5 Antifraude — mínimo antes de abrir el programa (29.5)

| Control | Regla |
|---|---|
| Email verificado | Sin verificación no hay activación |
| Dispositivo e IP | Hash propio (UA + zona horaria + pantalla + idioma; **sin fingerprinting de terceros**) y hash de IP con sal rotativa. **1 activación por dispositivo/IP cada 30 días** |
| Auto-referido | Mismo email normalizado, mismo dispositivo o misma cuenta OAuth → rechazo silencioso |
| Emails desechables | Lista pública de dominios desechables (MIT), actualizada mensualmente |
| Retardo | 7 días entre activación y abono |
| Velocidad | > 5 activaciones/semana por referente → cola de revisión manual en admin (29.6) |
| Clawback | Reembolso, baneo o fraude confirmado del referido → asiento `clawback` y escalera recalculada. **En el código (2026-10-02):** acción de admin (`POST /admin/economy/referrals/{id}/clawback`); recupera lo que quede de los 300 con un gasto FIFO, **sin saldo negativo** (lo gastado queda a la vista del admin, no como deuda), y si el referente baja de un hito pierde su premio, para no cobrarlo dos veces al volver a él |
| Transparencia | Todo esto se declara en la política de privacidad (ePrivacy/GDPR, interés legítimo antifraude) → 21.3 |

Objetivo: **fraude < 2 %** de las activaciones. Si supera el 5 % dos semanas seguidas,
el programa se pausa solo (flag) y avisa al dueño.

### 3.6 Qué esperar (benchmarks)

- Programas bien hechos traen **10–30 %** de los registros; Dropbox llegó al 35 %.
- Los usuarios referidos retienen mejor que los orgánicos; se mide en cohortes (29.6).
- **Amplifica lo que hay**: con Day-30 al 2 % no hay nada que referir. Por eso la
  Serie 29 se abre **después** de la 24 y con la retención base medida (ADR-32).

---

## 4. Códigos autogenerados — cinco tipos, no uno

### 4.1 Tipos

| Tipo | Quién lo emite | Para qué | Formato | Usos | Caduca |
|---|---|---|---|---|---|
| **Referido** | El sistema, 1 por usuario | §3 | `NOMBRE-7K2M` | ilimitados | nunca |
| **Campaña** | Dueño/admin, por canal y pieza | Créditos de bienvenida + **atribución**: cada vídeo, artículo, post o evento lleva el suyo | `YT-ES-03`, `DEV-BKT`, `HN-EN` | hasta `max_uses` | 90 días |
| **Lote de un solo uso** | Admin, en bloque (CSV) | Universidades (una clase), pilotos B2B, eventos, prensa | `UNAM-A3F9-X1` | 1 | fecha del lote |
| **Instructor** | Cada instructor del marketplace | Descuento a sus alumnos en su curso + atribución de sus ventas | `PROF-ANA-20` | ilimitados | mientras el curso esté activo |
| **Reactivación** | El sistema, automático | Email a 14 días de inactividad: «tienes 200 créditos que caducan en 72 h» | `VUELVE-9Q2` | 1 | 72 h |

### 4.2 Esquema (29.0)

```sql
promo_codes (
  id            bigserial primary key,
  code          text not null unique,
  kind          text not null,        -- campaign | batch | instructor | reactivation
  credits       integer not null default 0,
  discount_pct  smallint,             -- solo instructor
  instructor_id uuid, course_id uuid, -- solo instructor
  channel       text, campaign text,  -- atribución: youtube_es, devto, hn, uni, superteam…
  segment       text,                 -- student | switcher | senior | instructor | b2b | web3
  lang          text,                 -- es | en (ADR-17: un código no mezcla idiomas)
  max_uses      integer,              -- null = ilimitado
  uses          integer not null default 0,
  single_use    boolean not null default false,
  expires_at    timestamptz,
  batch_id      uuid,                 -- lotes
  created_by    uuid not null,
  created_at    timestamptz not null default now()
);
promo_redemptions (
  id bigserial primary key,
  code_id bigint not null references promo_codes(id),
  user_id uuid not null references users(id),
  ledger_id bigint references credit_ledger(id),
  created_at timestamptz not null default now(),
  unique (code_id, user_id)           -- idempotencia: un código, un usuario, una vez
);
referral_codes (user_id uuid primary key, code text not null unique, created_at timestamptz);
referrals (
  id bigserial primary key,
  referrer_id uuid not null, referred_id uuid not null unique,
  code text not null,
  status text not null,               -- pending | activated | rejected | clawed_back
  device_hash text, ip_hash text,
  fraud_flags jsonb not null default '[]',
  activated_at timestamptz, credited_at timestamptz,
  created_at timestamptz not null default now()
);
```

### 4.3 Reglas de formato y canje

- Alfabeto **sin `0 O 1 I L`**, mayúsculas, guiones como separador; 4–6 caracteres aleatorios.
- Canje **solo en web** (§1); la API rechaza el canje desde clientes nativos.
- Canje idempotente: `(code_id, user_id)` único; la misma petición dos veces no abona dos veces.
- Rate limit del endpoint de canje: 5 intentos/10 min por usuario e IP (reutiliza `RateLimiter` de 22.6).
- Un código lleva **idioma**: el de campaña ES no se muestra en EN ni al revés (ADR-17).

### 4.4 Los códigos son la analítica de canal

Con presupuesto cero no hay herramienta de atribución de pago. **El código de
campaña es la atribución.** Cada pieza publicada por las Series 26 y 27 lleva un
código único, y el admin (29.6) muestra por código: canjes → activaciones → pagos.
Así se sabe qué vídeo, qué artículo y qué comunidad convierten, sin terceros en prod
(línea roja 5). Convención en `DISTRIBUCION.md` §12.

---

## 5. API (29.1, 29.3, 29.4, 29.6)

| Método y ruta | Quién | Qué |
|---|---|---|
| `GET /credits/balance` | usuario | saldo y próximos vencimientos |
| `GET /credits/ledger?cursor=` | usuario | asientos paginados (22.6) |
| `POST /credits/spend` `{sink, ref_id}` | usuario | gasto FIFO; 409 si saldo insuficiente |
| `POST /codes/redeem` `{code}` | usuario, **solo web** | canje idempotente |
| `GET /referrals/me` | usuario | código, enlace, activaciones, escalera |
| `GET /economy/prices` | público | grifos y sumideros que el código cablea de verdad (2026-10-01: referidos y comodín de racha); la Cartera la pinta tal cual |
| `POST /admin/codes/batch` | owner | genera lote (CSV descargable) |
| `GET /admin/economy/attribution` | owner | canjes → activaciones → pagos por código/canal/campaña |
| `GET /admin/referrals` | owner | K-factor, % registros vía referido, cola de revisión, fraude |
| `POST /admin/referrals/{id}/review` | owner | aprobar / rechazar / clawback |

Todo en `/api/v1`, documentado en `API.md` (guardia 20.3) y con tests de autorización.

---

## 6. Admin (dentro de 22.1, tarea 29.6)

- **Economía:** créditos emitidos/gastados/caducados por día; ratio sumidero/grifo;
  top consumibles; alerta si emisión > gasto × 3 durante 30 días (inflación).
- **Referidos:** invitaciones, registros, activaciones, K-factor, % de registros vía
  referido, retención D7/D30 referidos vs orgánicos, cola de revisión, tasa de fraude.
- **Códigos:** generación de lotes, uso por código, atribución por canal/campaña,
  export CSV. Todo **filtrable por idioma** (23.4).

---

## 7. Métricas y objetivos (se suman a ADR-32)

| Métrica | Mes 3 | Mes 6 | Mes 12 | Benchmark |
|---|---|---|---|---|
| % registros vía referido | 5 % | 15 % | 25 % | 10–30 % programas maduros; Dropbox 35 % |
| K-factor (invitaciones × conversión) | 0,1 | 0,3 | 0,5 | > 0,5 es viral; edtech rara vez pasa de 0,3 |
| Fraude en activaciones | < 2 % | < 2 % | < 2 % | — |
| Retención D30 referidos vs orgánicos | +30 % relativo | +30 % | +30 % | referidos retienen mejor |
| Tasa de canje de códigos de campaña | 10 % | 15 % | 20 % | de los que ven la pieza y llegan |
| Retorno por código de reactivación | 8 % | 12 % | 15 % | email win-back típico 5–10 % |
| Ratio sumidero/grifo | ≥ 0,6 | ≥ 0,7 | ≥ 0,8 | < 0,5 = inflación |

---

## 8. Por segmento (ver `SEGMENTOS.md` §«Créditos, referidos y códigos por segmento»)

| Segmento | Grifo principal | Sumidero principal | Referido | Código típico |
|---|---|---|---|---|
| Estudiante | racha, módulos | simulacros, congelar racha | escalera hasta 1 mes Pro | campaña YouTube/TikTok ES |
| Career-switcher | proyectos, simulacros | informe PDF, bootcamp | certificación a los 10 | campaña LinkedIn, universidades |
| Developer Senior | skip confirmado por BKT | bootcamp async | refiere colegas → bootcamp | campaña Dev.to/HN |
| Profesor / Instructor | no gana créditos | — | su código de instructor | `PROF-…` |
| Empresa | bolsa de empresa por módulos | seats extra | — | lote de un solo uso para empleados |
| Web3 / Solana | módulos de track32 | simulacros, proyectos | escalera estándar | `ST-MX`, `ST-AR` (eventos Superteam) |

---

## 9. Dónde entra en las series (sin ampliar el alcance de cada una)

| Pieza | Serie / tarea |
|---|---|
| Schema, servicio, precios, referidos, códigos, antifraude, admin, reactivación, UI | **Serie 29** (29.0–29.8) |
| Cláusulas legales | 29.11 → 21.7; antifraude → 21.3 |
| Métricas en admin | 22.1 (fila ampliada) + 29.6 |
| Wallet, escalera y canje en la UI | 24.6 (junto a 29.8) |
| Códigos de campaña en cada pieza | 26.x y 27.x (cada tarea lleva su código) + 26.8 / 27.9 |
| Código de instructor | 28.1 |
| Payouts USDC | 28.7 + 29.9 |
| Certificados verificables | 29.10 + 24.7 |
| track32 Solana/Web3 | 37.8 (nivel C, ADR-53) |

---

## 10. USDC como rail — no como activo (ADR-36)

**Problema real:** un estudiante en Argentina o Venezuela no puede pagar $14,99 con
tarjeta; un instructor en Colombia no puede cobrar por Stripe Connect.

**Solución sin token:**

| Uso | Cómo | Coste | Condición |
|---|---|---|---|
| Cobro de suscripciones en LATAM | Stripe *Pay with Crypto*: el cliente paga USDC (Solana, Ethereum, Polygon, Base), Stripe **liquida en fiat** a Whetzy, ~1,5 % | 0 $ de integración extra sobre 7.2 | Solo si H.19 elige Stripe. Si elige un MoR (Paddle/Lemon Squeezy), se documenta la alternativa del MoR o se descarta |
| Payouts a instructores fuera de Stripe Connect | USDC en Solana (fee ≈ $0,001) o Wise; el instructor elige y declara sus impuestos | 0 $ | KYC del instructor (28.0) y fiscalidad según 21.1 |

**Lo que no se hace:** custodiar cripto de usuarios, tener wallet caliente con
saldo, cotizar precios en cripto, aceptar cualquier cosa que no sea USDC liquidado
en fiat. Whetzy nunca «tiene» cripto en balance.

---

## 11. Credenciales verificables — sin token (ADR-37)

| Capa | Qué | Coste | Estado |
|---|---|---|---|
| **Open Badges 3.0** (1EdTech, = W3C Verifiable Credentials) | Cada certificado de track/simulacro es un JSON-LD firmado por Whetzy, con endpoint público de verificación y revocación. Es lo que reconocen LinkedIn, Credly y los empleadores | 0 $ | 29.10 (obligatorio) |
| Página pública `whetzy.com/verify/<código>` | Ya existe `GET /api/v1/exams/certificates/{code}`; se le añade el JSON-LD y el QR | 0 $ | 29.10 |
| **cNFT en Solana** (opcional) | Copia pública, **no transferible** (soulbound), ~0,0001 $ por emisión; requiere una wallet emisora con unos céntimos de SOL | ≈ €3–5 una vez | **H.27** (ADR-15: gasto con alternativa gratuita = solo Open Badges) |

Nunca: token fungible, NFT vendible, «staking» de certificados.

---

## 12. Lo que se rechazó y por qué (resumen de ADR-33)

| Promesa del token | Evidencia |
|---|---|
| «No existe en el mercado» | Sí existe y falló: Open Campus (EDU, 2023, Animoca; token muy por debajo de máximos y uso marginal), BitDegree (BDG, 2017), STEPN y Axie (reflexividad). Coinbase/Binance *Learn & Earn* funcionan porque **un exchange paga con dinero real como marketing**. Ver `COMPETENCIA.md` §2.6 |
| «Retención» | Recompensa extrínseca con precio de mercado desplaza la motivación intrínseca; el usuario optimiza el token, no la skill |
| «100 casos de uso» | Cinco reales (§0), y todos funcionan mejor sin token |
| «Valoración» | Los adquirentes edtech (DataCamp, Coursera, Skillsoft, Pearson) tratan un token vivo como pasivo legal |
| «Coste cero» | Crear el SPL token cuesta céntimos; darle valor cuesta liquidez, opinión legal (MiCA, Chipre/UE), auditoría y KYC |
| **Daño específico a Whetzy** | Bots farmeando las 10.989 preguntas del banco (2026-09-30) **envenenan BKT/FSRS/DKT**. El único activo diferencial se degrada desde dentro |

Si el dueño quisiera reabrirlo, la condición mínima es una opinión legal MiCA fechada
y un plan de liquidez con capital propio — ambos son HUMAN-BLOCKED con € (ADR-15).

---

## 13. Serie 29 — resumen de tareas (detalle en `AUTONOMOUS_STATE.md`)

| ID | Tarea |
|---|---|
| 29.0 | Schema: `credit_ledger`, `promo_codes`, `promo_redemptions`, `referral_codes`, `referrals` |
| 29.1 | Servicio de créditos: abono/gasto/caducidad FIFO, idempotencia, topes, tests |
| 29.2 | `content/economy/credits.json` (grifos y sumideros versionados) + `GET /economy/prices` |
| 29.3 | Referidos: código, enlace por idioma, evento de activación, retardo, escalera con entitlements |
| 29.4 | Códigos: 5 tipos, lotes, formato seguro, canje solo web |
| 29.5 | Antifraude: hashes propios, límites, cola de revisión, clawback, pausa automática |
| 29.6 | Admin: economía, referidos, atribución por código, export |
| 29.7 | Reactivación automática (cola 22.6) con email ES/EN nativo |
| 29.8 | UI: wallet, escalera, canje (sesión interactiva; con 24.6) |
| 29.9 | USDC como rail (tras H.19) + payouts USDC/Wise (con 28.7) |
| 29.10 | Credenciales verificables Open Badges 3.0 (+ cNFT tras H.27) |
| 29.11 | Cláusulas legales de créditos, referidos y antifraude → 21.7 / 21.3 |
| 29.12 | Scorecard: métricas §7 en admin; verificación adversaria de toda la serie |
