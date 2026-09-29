# Whetzy — Inteligencia Competitiva Exhaustiva

> **Documento vivo nº 14.** Análisis directo + indirecto. Última actualización:
> **2026-09-28** (§A.2c, capturas de pantalla 24.0; §A.2b, Brilliant y Kodree; resto de §A del 2026-09-24). **§A manda sobre §1–§3**, que son del
> 2026-09-18 y contienen cifras que no se comprobaron entonces y hoy no se
> sostienen (precios de Boot.dev y Platzi, ingresos): léelas como hipótesis.

---

## A. Captura en vivo del 2026-09-24 (manda sobre §1–§3)

**Método.** Páginas públicas, sin registrarse, sin saltar CAPTCHA ni antibots
(Udemy, DataCamp `/pricing`, TryHackMe `/pricing`, Exercism y LeetCode respondieron
403 o checkpoint y se dejaron). La salida de red está en EE. UU.: los precios son
los que esas webs sirven allí y en USD. Cuatro agentes recogieron 33 sitios. Sus
informes y los extractos de texto quedan fuera del repo (datos de terceros). Aquí
se separa lo que **se volvió a descargar y leer a mano** de lo que **solo
reportó un agente**.

### A.1 Comprobado a mano (re-descarga del 2026-09-24)

| Competidor | Dato | Evidencia en la página | URL |
|---|---|---|---|
| Codecademy | Plus **$14.99/mes** anual o **$29.99** mensual; Pro **$19.99** anual o **$39.99** mensual; All Access **$54.99/mes** anual; Basic gratis | «$14.99 a month, billed annually or $29.99 billed monthly», «Our free Basic plan» | codecademy.com/pricing |
| Codecademy | Sin web en español | `codecademy.com/es` redirige a la home, `lang="en"` | — |
| Boot.dev | **$59/mes** o **$399/año** ($33/mes) | JSON-LD `"price":"59"`, «$33 / month $399 / year, billed yearly» | boot.dev/pricing |
| Platzi | Basic **$49/mes**; Expert **$249/año** (se anuncia como $21/mes, 4 cuotas de $63); hay cursos gratis | `"planPrice":"249"`, `"priceMonth":"49"`, FAQ «¿Hay cursos gratis…?» | platzi.com/precios/ |
| EDteam | Premium **$30** mensual, **$180** semestral, **$240** anual (tachado $360, «el mes te sale a $20»); plan gratuito de **9 cursos** con certificado | `"premiumPricing":{"monthly":{"price":30…},"annual":{"price":240,"basePrice":360}}` | ed.team/premium |

Estas cifras son las que muestra la comparativa de la landing
(`frontend/src/lib/comparison.ts`, fecha `COMPARISON_CHECKED_ON`). Un test
(`src/test/comparison.contract.test.ts`) exige fecha y una celda por competidor.
Si cambias una cifra, re-descarga la página y cambia la fecha.

### A.2 Reportado por agentes, no reproducido (tratar como «probable»)

- **Precios.**
  - Sololearn PRO $69.99/año o $12.99/mes; MAX $119.88/año.
  - Mimo Pro $9.99/mes (anual) o $14.99; Max $24.99 o $39.99. El acceso web solo está en Max.
  - Brilliant $20/mes (anual) o $30.
  - Khanmigo $4/mes.
  - Enki desde $4/mes.
  - Educative $13–21/mes (anual).
  - Codewars Red $5.
  - Coursera Plus $59/mes o $399/año.
  - Pluralsight $30–55/mes.
  - AWS Skill Builder $29/mes; examen Foundational $100, Associate $150.
  - HTB Academy: exámenes de $490 y $1260.
  - W3Schools: examen de Python $95.
  - UltraCamp (antes OpenBootcamp) 19 €/mes.
  - Coderhouse: curso de Python 268.800 ARS / 4.048 MXN / 446 € con promoción.
  - Henry: financiación AIC por USD 4.000 en total.
- **Localización.**
  - Boot.dev aplica paridad de poder adquisitivo (según su FAQ).
  - DataCamp tiene selector de moneda con MXN y BRL.
  - EDteam fija precio local en BO/CO/MX/PE.
- **Mecánicas.**
  - Duolingo ofrece streak freeze y ligas.
  - Sololearn usa 5 corazones con recarga de 5 h, y dice de sus ligas que son «Entirely optional».
  - Mimo vende la reparación de racha en su plan de pago.
  - Educative ofrece «1-minute assessment» para saltar lo que ya sabes.
  - Boot.dev tiene «Training Grounds» con repetición espaciada.
- **Certificaciones.**
  - AWS y Microsoft examinan en español, pero la práctica oficial es en inglés. Microsoft escribe «Practice Assessments will be available in local languages soon».
  - Ningún preparador de la muestra muestra un *readiness* por dominio ponderado por el exam guide.
  - Ninguno usa Open Badges 3.0: Credly en AWS y THM, ID propio en HTB, QR en W3Schools.

La última tanda es una **afirmación de ausencia** sobre las páginas que vieron los
agentes, no sobre los productos por dentro.

### A.2b Captura del 2026-09-28: Brilliant y Kodree

Dos agentes (uno por producto) y re-descarga a mano de las cifras que
sostienen la comparación. Mismo método que §A: páginas públicas, sin cuenta,
salida de red en EE. UU. Trustpilot devolvió 403 a la descarga directa: sus
cifras no están aquí.

**Comprobado a mano (2026-09-28)**

| Competidor | Dato | Evidencia en la página | URL |
|---|---|---|---|
| Brilliant | **$27.99/mes** o **$161.88/año**; sustituye a «$20 o $30» de §A.2 | valores `27.99` y `161.88` en el HTML de la suscripción | brilliant.org/subscribe/ |
| Brilliant | Gratis: 2 lecciones al día | «2 keys per day»; Premium «no keys required» | brilliant.org/help/pricing-and-plans/what-s-the-difference-between-free-and-premium/ |
| Brilliant | Sin certificados | «does not currently offer completion certificates, course credits, academic degrees, or professional certifications» | brilliant.org/help/using-brilliant/does-brilliant-offer-certificates/ |
| Brilliant | iOS 4,7★ / 32.677 valoraciones; solo inglés | JSON-LD `"ratingValue":4.7`, `"reviewCount":32677`; «Languages English» | apps.apple.com/us/app/id913335252 |
| Kodree | **$39.99/mes**, **$98.99/año** ($8.25/mes), **$199.99** de por vida; sin plan gratis | precios en el HTML de la home | kodree.com |
| Kodree | Reembolso en 14 días solo si se completó un módulo | «within 14 days of the initial purchase… by completing at least one module» | kodree.com/subscription-terms |
| Kodree | «60+ COURSES»; iOS 4,42★ / 248; solo EN | iTunes Lookup API, `languageCodesISO2A: ["EN"]`, versión del 2026-09-25 | itunes.apple.com/lookup?id=6739421200 |
| Kodree | Android 4,32★ / 631 | JSON-LD `ratingValue`, `ratingCount` | play.google.com (`com.mateacademyapp.knowely`) |
| Kodree | Web solo en inglés; `/try-free` enlaza a la marca antigua | `lang="en"`; 9 enlaces a `app.knowely.com` | kodree.com/try-free |

**Reportado por agentes, no reproducido (probable)**

- **Brilliant.**
  - Tutor IA «Koji» (mayo de 2026): voz de ElevenLabs, dibuja en pantalla y no da la respuesta. No se publica qué modelo usa.
  - Ligas semanales por XP y rachas.
  - Plan familiar $45/mes para 6 plazas.
  - Gratis para profesores y sus clases; `/for-teams` da 404.
  - Reembolsos «solely as a courtesy»; quejas por renovaciones no esperadas (PissedConsumer 1,8/5).
  - Programación solo conceptual, en Python.
- **Kodree.**
  - Antes se llamaba Knowely (cambio el 2025-07-23); es del equipo de Mate Academy.
  - Siete rutas de carrera: Data Analyst, Front-End, Full-stack, Python, UX/UI, Project Management y Vibe Coding.
  - Unos 3 proyectos de portafolio por ruta; editor de código en el navegador; «AI Buddy», sin proveedor declarado.
  - XP, ligas e insignias.
  - Certificados que sus términos no presentan como título oficial: «does not award any official documents on education».
  - Renovaciones no reembolsables.
  - Entidades en Chipre y Delaware.
  - Sin oferta B2B encontrada.

**Lo que tienen y Whetzy no, frente a lo que el plan ya cubre** (revisado contra
`AUTONOMOUS_STATE.md` y `CATALOGO_MAESTRO.md` el 2026-09-28):

| Lo que tienen | ¿En el plan? | Dónde |
|---|---|---|
| Apps publicadas en iOS y Android | Sí, pero depende del dueño | serie 17, 19.2, H.2/H.3 |
| Proyectos de portafolio | Sí | 37.11 (10 por track ejecutable; BLOCKED por 37.6) |
| Rutas por rol | Parcial | bootcamps 19.4 (3), roadmap por rol 19.8 |
| Vídeo o animación de conceptos | Sí, pasivo | Manim 14.14, 18.9, 19.10 |
| Problemas visuales **manipulables** (Brilliant) | **No** | ninguna fila |
| Tutor por **voz** o que dibuja | **No** | ninguna fila |
| Comunidad dentro de la app | **No** | solo perfiles externos (26.7) |
| Plan anual | Sí (40.9) | como la competencia directa (dueño, 2026-09-28) |
| Plan de por vida o familiar | **No, a propósito** | el dueño los descartó el 2026-09-28: solo mensual y anual |
| UX/UI, Excel o Power BI | **No** | `CATALOGO_MAESTRO.md` §2.0.1: ux-design «no se proponen todavía» |
| Java o TypeScript ejecutables | Parcial | 37.8 añade tracks; runtimes solo Python/SQL/JS |

### A.2c Capturas de pantalla del 2026-09-28 (24.0, landing + precios)

Primera parte ejecutable de 24.0 sin cuentas de terceros (instrucción explícita del
dueño de sesión: «sin cuentas externas»). Playwright/Chromium, páginas públicas,
sin login, sin saltar ningún CAPTCHA/Turnstile — se retrocedió donde apareció uno.
21 capturas (landing desktop 1440×900, landing mobile 390×844, precios) para 7 de
los 8 competidores de §1 en `docs/competencia-screenshots/` (gitignoreada, ADR-46;
entregadas al dueño de sesión directamente, no van al repo).

**Comprobado a mano sobre la captura (2026-09-28):**

| Competidor | Dato nuevo o confirmado | Evidencia |
|---|---|---|
| Boot.dev | Confirma §A.1: $33/mes facturado anual, $399/año, toggle "Yearly -44%" | `bootdev-pricing.png` |
| Codecademy | Confirma §A.1 exacto: Plus $14.99/mes anual ($29.99 mensual), Pro $19.99/mes anual ($39.99 mensual), Basic gratis | `codecademy-pricing.png` |
| DataCamp | **Nuevo** (§A decía 403/checkpoint el 2026-09-24, no se había reproducido): Basic gratis, Premium $35/mes, Teams $28/usuario/mes | `datacamp-pricing.png` |
| Educative | Afina el rango «probable» $13–21/mes de §A.2: Standard $12/mes ($139/año, 50% off), Premium $16/mes ($189/año), Premium Plus $21/mes ($239/año) — precios con descuento activo, no de lista | `educative-pricing.png` |
| Brilliant | **Discrepancia sin resolver entre dos páginas del propio Brilliant el mismo día**: `/premium/` (esta captura) muestra Monthly $30, Annual $20/mes, Family $40/mes/6 plazas; §A.2b (misma fecha, `/subscribe/`) registró $27.99/mes o $161.88/año. No es un error de esta sesión — son dos páginas de precios distintas y no coincide ninguna de las tres cifras con ninguna de las dos. Sin decidir cuál es la vigente | `brilliant-pricing.png` |
| TryHackMe | Landing y nav de precios cargan bien; el panel de precios en sí no renderizó a tiempo (carga diferida) en el primer intento, y el segundo intento devolvió un «Vercel Security Checkpoint» — no reintentado más, se trata como bloqueo | `tryhackme-pricing.png` (sin cifras) |
| Platzi | Landing y precios cargan; el panel de precios no quedó dentro del viewport capturado (scroll cayó en testimonios). §A.1 ya tiene Basic $49/mes y Expert $249/año verificados por otra vía — no se repite la re-descarga aquí | `platzi-pricing.png` (sin cifras nuevas) |
| Platzi (reintento 2026-09-29) | `/planes/` devolvió «Hay un firewall… espera un momento y vuelve a intentarlo» — un bloqueo nuevo que no estaba el 2026-09-28, no un fallo de scroll. Tratado igual que TryHackMe/Exercism: sin reintentar, sin saltarlo | sin captura |
| Exercism | **Bloqueado**: Cloudflare Turnstile con checkbox interactivo («Performing security verification»), no un simple 403. No se intentó resolver el reto — cae fuera de «páginas públicas sin saltar antibots» | sin captura |

**Lo que esto NO cierra en 24.0:** onboarding (pasos 1-5), dashboard autenticado y
gamificación de los 8 competidores requieren cuenta — excluidos explícitamente esta
sesión. Sigue faltando `docs/design/decisiones-24.0.md` con la decisión del dueño
pantalla a pantalla. El criterio completo («8 × ≥5 capturas») tampoco se cumple:
esta tanda es 3 por competidor (7/8), no 5.

### A.3 La lógica de negocio del mercado, y dónde encaja Whetzy

**Cinco modelos, cinco anclas de precio.**

1. **Suscripción de catálogo** (Codecademy, Platzi, EDteam, DataCamp, Pluralsight, Coursera Plus).
   - Ancla: **$14.99–21 al mes pagando el año**; $29–59 si es mensual.
   - El descuento anual va del 33 % al 58 %, y es la palanca principal de caja por adelantado.
   - Retienen por catálogo (miles de cursos) y certificado de finalización.
2. **Freemium de hábito en móvil** (Duolingo, Mimo, Sololearn).
   - Monetizan el hábito: racha, ligas y **límites al error** (corazones).
   - La IA es el nivel más caro.
   - El contenido es gratis; lo que se vende es la fricción que se quita.
3. **Bootcamp de ticket alto** (Coderhouse, Henry).
   - Venden empleabilidad con cuotas, financiación ligada a ingresos (ISA/AIC) y cuentas atrás de «70 % OFF».
   - Ticket: cientos a miles de USD.
4. **Preparación de certificación** (AWS, Microsoft Learn, HTB, THM, W3Schools).
   - El fabricante regala la formación y cobra el examen ($95–$490).
   - En B2B, la palanca es el voucher.
5. **Gratis de referencia** (freeCodeCamp, CS50, Microsoft Learn).
   - Fijan el suelo: Python básico con certificado **ya cuesta $0**.

**Qué vende Whetzy que el resto no combina.** Tres cosas medidas por el motor, no
por el calendario: dominio (BKT), retención (FSRS) y preparación para el examen.
Todo en ES y EN nativos, con ejecución en el navegador. Cada modelo del mercado
cubre una parte:
- el de catálogo, amplitud;
- el de hábito, constancia;
- el de certificación, examen;
- ninguno, en español, el conjunto «sé que lo sabes y sé si apruebas».

**Factores ligados a Whetzy, y qué implican.**

1. **Coste marginal.**
   - El contenido cuesta ~0 (banco propio con fuentes libres, ADR-11). Lo variable es el tutor LLM (Groq) y la infraestructura.
   - Por eso el plan gratuito puede llevar **todo el contenido y el motor**, pero el tutor necesita cupo.
   - Es el mismo corte que hacen Mimo, Sololearn y Brilliant, pero sin cobrar por equivocarse.
2. **El suelo es $0.**
   - Cobrar por Python básico compite con freeCodeCamp y CS50.
   - Lo cobrable es lo que el gratis no da: repaso que mantiene, *readiness* por dominio para AWS/Azure/ISC2 en español, y el tutor con el contexto de lo que dominas.
3. **Precio en LatAm.**
   - El mercado hispano paga en moneda local y a plazos: MSI en México, cuotas en Argentina.
   - Castiga la desconfianza: las cuentas atrás de Coderhouse y Henry.
   - Una tarifa regional explicada («si ves tu moneda, ya tienes el ajuste de tu país») y sin falsas urgencias es diferencial. Boot.dev y DataCamp lo hacen en inglés; en español, EDteam lo hace en cuatro países.
4. **La confianza como activo.**
   - Whetzy acaba de quitar testimonios y cifras inventadas de su landing (30.1).
   - Una comparativa fechada y con fuente, y un precio público, convierten esa corrección en una ventaja de marca.
5. **Distribución.**
   - Los de catálogo compran tráfico. Los de hábito viven de la tienda de apps.
   - Whetzy, con canales de coste $0 (DISTRIBUCION.md), depende de contenido orgánico bilingüe y de que el alumno comparta su *readiness* o su credencial verificable.

**Precio: corrección de premisas de ADR-21.** ADR-21 fijó Pro en $14.99/mes con estas
premisas:
- «Boot.dev $49/mes»: hoy es **$59** mensual o **$33** pagando el año;
- «Codecademy $24.99/mes»: hoy es **$29.99** Plus mensual, **$14.99** anual.

La decisión sigue en pie; lo que cambia es la lectura. **$14.99 mensual queda por
debajo de todos los de catálogo verificados** ($29.99 / $49 / $30 / $59), y es igual
a lo que cobran al mes pagando el año. Falta, y es decisión del dueño (H.35):
- el precio anual;
- si hay tarifa regional;
- qué entra en el plan gratuito.

**Actualización 2026-09-24 (ADR-41):** el dueño fijó los mensuales:
- Pro, 14,99 $;
- Pro Max, 19,99 $;
- Creador, 99,99 $ (80/20 por venta).

Son los que muestran la landing y la comparativa. Siguen pendientes (H.35) el anual, la
tarifa regional y qué añade Pro Max.

### A.4 Lo que se adopta, y lo que no

| Idea | Origen | Decisión | Ledger |
|---|---|---|---|
| Comparativa pública fechada y con fuente | (propia, contra la landing inventada de antes) | **Hecho**: 4 filas, 3 competidores | 35.1 |
| Diagnóstico visible de «salta lo que ya sabes» | Educative | Adoptar: el *placement* ya existe; hacerlo visible en cada track | 35.2 |
| Racha amable: comodines gratis y «perder la racha no borra lo aprendido» | Duolingo (freeze), contra Mimo (reparación de pago) | Adoptar | 35.3 |
| Corazones o vidas | Sololearn, Duolingo | **No**: el error alimenta al motor, no se cobra | — |
| Ligas | Duolingo, Sololearn | Solo *opt-in* visible | 35.4 |
| Tarifa regional, anual en cuotas | Boot.dev, DataCamp, EDteam, Platzi | Propuesta al dueño | H.35 |
| *Readiness* por dominio ponderado por el exam guide, en ES | hueco reportado (A.2) | Producto estrella de las rutas cloud y seguridad | 35.5 |
| Open Badges 3.0 con verificación pública | hueco reportado (A.2) | Ya en ECONOMIA.md (S29); priorizar tras 35.5 | — |
| Cuentas atrás y «70 % OFF» permanentes | Coderhouse, Henry | **No** | — |

---

## 0. Marco de análisis

Para cada competidor se documenta:
1. **Modelo de negocio** (pricing, conversión, revenue conocido)
2. **Fortalezas reales** (qué hacen mejor que nadie)
3. **Debilidades reales** (dónde falla o no cubre)
4. **Qué adaptar al estilo Whetzy** (ideas, nunca código ni contenido)
5. **Qué evitar** (lo que no funciona o que Whetzy no debe ser)

---

## 1. Competencia Directa

### 1.1 Boot.dev

**URL:** boot.dev | **Free tier:** ✅ primeros módulos de cada track

**Modelo:**
- $49/mo o $348/yr (plan anual)
- ~25,000 paying members → ~$10M ARR
- Team ~13 personas, bootstrapped, sin VC

**Fortalezas reales:**
- Diseño RPG inmersivo: mapa del mundo con ciudades = tracks, el usuario "viaja"
- Racha diaria con personalidad — el personaje "muere" si pierdes la racha
- Canal YouTube 100K+ subs que genera adquisición orgánica constante
- Comunidad Discord muy activa (~30K miembros)
- Foco brutal en un nicho: backend developer (Python, Go, SQL)
- El fundador (Lane Wagner) es la cara visible — auténtico y cercano

**Debilidades reales:**
- Motor de aprendizaje lineal — no adaptativo
- Solo en inglés — cero presencia española
- 5 tracks principales — catálogo pequeño vs Platzi o DataCamp
- Sin certificaciones de terceros — solo "certificado Boot.dev"
- Sin módulo de IA/ML profundo — su nicho es backend, no AI engineer
- Sin ciberseguridad

**Qué adaptar al estilo Whetzy:**
- El mapa visual de progreso — hacer el BKT visible como "territorio conquistado"
- La personalidad de la racha — no copiarla, crear la propia con identidad Python/AI
- El formato del canal YouTube — tutoriales que usan la plataforma en vivo
- La relación fundador-comunidad — el dueño es el mejor embajador

**Qué evitar:**
- No tener motor adaptativo en el corazón (el mayor diferenciador de Whetzy)
- La narrativa RPG fantasía no encaja con el tono profesional de Python→AI Engineer

---

### 1.2 DataCamp

**URL:** datacamp.com | **Free tier:** ✅ primeros capítulos de cada curso

**Modelo:**
- $39/mo individual o $399/yr
- B2B ~$300/seat/yr — 66% del revenue total
- ~$100M ARR (proyectado 2026), 18-19M learners, 6,000 B2B customers
- Adquirió Optima (adaptive learning) en nov 2025

**Fortalezas reales:**
- Motor adaptativo real (Optima) — pacing en tiempo real
- Profundidad en Python/R/SQL/data science — 730+ cursos
- B2B contracts con 80% del Fortune 1000
- Editor de código en browser — sin configuración
- Proyectos con datos reales (datasets de Kaggle, etc.)
- Certificaciones propias reconocidas en data science

**Debilidades reales:**
- Solo en inglés y árabe — cero español
- No cubre ciberseguridad, DevOps, móvil, o system design
- No cubre tracks de AI engineer completos (LLMs, agentes, RAG)
- No tiene gamificación — es producto corporativo, no consumer
- Precio alto para mercado LATAM ($39/mo = 70-100% de un salario mínimo/semana)
- B2B-first: experiencia consumer es secundaria

**Qué adaptar al estilo Whetzy:**
- Editor de código en browser sin instalación (ya implementado en Whetzy via JS sandbox)
- Proyectos con datos reales en cada track intermedio/avanzado
- Dashboard de empresa con métricas por empleado (Serie 22)
- Profundidad curricular por dominio (§7 quality gate ya lo exige)

**Qué evitar:**
- La frialdad corporativa — Whetzy tiene personalidad, DataCamp no
- Depender del 66% de revenue B2B sin base consumer sólida

---

### 1.3 Platzi

**URL:** platzi.com | **Free tier:** ✅ primeras clases de cada curso

**Modelo:**
- ~$29/mo o $149/yr ("Platzi Expert")
- 7M+ estudiantes, 4,000+ empresas
- Serie B de $62M (Prosus, dic 2021) — sin ronda desde entonces
- Estimaciones de revenue: $15M-$115M (muy divergentes, no verificadas)

**Fortalezas reales:**
- Marca dominante en español tech education — 11 años
- 1,900+ cursos en español nativo de alta calidad
- 70% completion rate (vs 10-15% industria) — dato diferenciador clave
- Comunidad enorme: Discord, Slack, foros propios
- B2B consolidado: 4,000+ empresas clientes
- Integración con LinkedIn para certificados

**Debilidades reales:**
- Formato video/cohort — NO adaptativo
- El "AI tutor" (Leap, adquirido jul 2026) es overlay conversacional, no motor real
- Sin certificaciones de terceros verificables (AWS, CompTIA, ISC2)
- Precio percibido como alto en LATAM para la calidad de retención real
- 1,900 cursos pero poca profundidad por track — muchos cursos de 2-4 horas
- Sin editor de código en browser — aprenden viendo, no haciendo

**Qué adaptar al estilo Whetzy:**
- El 70% completion rate como promesa de marca — superar este número y comunicarlo
- La producción de video — cursos Platzi tienen nivel de producción alto
- La integración con LinkedIn para certificados — validar con empleadores desde el día 1

**Qué evitar:**
- El modelo video — Whetzy es interactivo, no pasivo
- Crecer en cantidad de cursos antes de profundizar los existentes

---

### 1.4 Educative.io

**URL:** educative.io | **Free tier:** ✅ primeras lecciones

**Modelo:**
- ~$20/mo individual o $199/yr
- ~$98M ARR estimado (GetLatka 2025)
- ~892 empleados, ~$14.6M raised total (bootstrapped-style)
- Foco: interview prep, system design, Python, AI/ML

**Fortalezas reales:**
- Texto + código ejecutable en browser — sin video, sin instalar nada
- Paths muy bien estructurados para interview prep
- Precio accesible ($20/mo)
- Calidad de contenido alta en system design y Python avanzado

**Debilidades reales:**
- Motor de aprendizaje parcialmente adaptativo — no BKT+FSRS completo
- Solo inglés
- Sin gamificación real
- Sin certificaciones de terceros
- Sin comunidad activa
- UI anticuada comparada con Boot.dev o Brilliant

**Qué adaptar al estilo Whetzy:**
- El formato texto+código ejecutable sin video (ya implementado)
- Los paths de interview prep como track complementario (Algoritmos, track16)

---

### 1.5 TryHackMe

**URL:** tryhackme.com | **Free tier:** ✅ 77% del contenido es gratuito

**Modelo:**
- ~$10.50/mo anual
- 6M+ learners, $10M+ revenue
- Bootstrapped, creció con eventos gamificados (Advent of Cyber)
- Foco exclusivo: ciberseguridad

**Fortalezas reales:**
- Gamificación de ciberseguridad excelente: "Rooms" como misiones, rankings, badges
- 77% del contenido gratuito — bajo friction de entrada
- Advent of Cyber (evento anual) genera 100K+ registros nuevos
- Laboratorios virtuales en browser — practicar hacking sin instalar nada
- Comunidad muy activa en Discord y foros

**Debilidades reales:**
- Solo ciberseguridad — sin Python, sin AI, sin cloud
- Solo inglés
- Sin motor adaptativo — paths lineales
- Sin certificaciones de terceros directamente

**Qué adaptar al estilo Whetzy:**
- El modelo freemium generoso (77% free) como estrategia de adquisición
- Los eventos gamificados estacionales como motor viral (idea: "Python AI Challenge" anual)
- Los laboratorios virtuales — Whetzy ya tiene JS/Python executor

---

### 1.6 Codecademy

**URL:** codecademy.com | **Free tier:** ✅ ejercicios básicos

**Modelo:**
- ~$24.99/mo o $199/yr
- ~40M registered learners
- Adquirida por Skillsoft (~$525M en 2022)
- Revenue ~$50M ARR (en el momento de adquisición)

**Fortalezas reales:**
- Reconocimiento de marca enorme — el "primer lugar" donde muchos aprenden a programar
- Editor integrado en browser muy pulido
- Feedback inmediato línea por línea
- Career paths bien definidos con proyectos

**Debilidades reales:**
- Sin motor adaptativo — completamente lineal
- Bajo profundidad en AI/ML — cursos muy introductorios
- Sin certificaciones de terceros
- Adquirida por Skillsoft (en dificultades financieras) — futuro incierto
- Sin español nativo
- Gamificación básica comparada con Boot.dev

**Qué adaptar al estilo Whetzy:**
- El feedback inmediato del editor — ya implementado
- El reconocimiento de marca a través de la calidad del onboarding

---

### 1.7 Brilliant

**URL:** brilliant.org | **Free tier:** ✅ primeras lecciones

**Modelo:**
- ~$24.99/mo o $149/yr
- ~10M+ users
- ~$14M ARR estimado (GetLatka 2024)
- Foco: STEM, matemáticas, CS, ciencias

**Fortalezas reales:**
- Visualizaciones interactivas extraordinarias — hace visible lo abstracto
- Motor de aprendizaje basado en problemas (no memorización)
- Diseño visual impecable — la UI más bella del sector educativo
- Feedback que explica el error, no solo dice "incorrecto"

**Debilidades reales:**
- No cubre Python/AI Engineering como carrera — es STEM general
- Sin certificaciones de mercado laboral
- Sin comunidad
- Muy caro para lo que ofrece en términos de empleabilidad directa
- Solo inglés

**Qué adaptar al estilo Whetzy:**
- Las visualizaciones interactivas para conceptos abstractos (ej: visualizar BKT, redes neuronales)
- El diseño UI como referencia de calidad — es el estándar a superar
- El feedback explicativo — no solo "incorrecto" sino "por qué y cómo arreglarlo"

---

### 1.8 Exercism

**URL:** exercism.org | **Free tier:** ✅ 100% gratuito

**Modelo:**
- Gratuito — organización sin ánimo de lucro
- Donaciones + sponsors
- 50+ tracks de lenguajes, mentoring humano

**Fortalezas reales:**
- 100% gratuito — cero friction
- Mentoring real de developers voluntarios
- Ejercicios de alta calidad verificados por comunidad
- MIT license — fuente [reusar] para Whetzy

**Debilidades reales:**
- Sin motor adaptativo — el usuario elige ejercicios
- Sin ruta de carrera clara
- Sin certificaciones
- Sin gamificación
- UI básica

**Qué adaptar al estilo Whetzy:**
- Los ejercicios (MIT license) como fuente de contenido ejecutable
- El modelo de mentoring como feature premium futuro (marketplace de profesores)

---

## 2. Competencia Indirecta

### 2.1 YouTube educativo

**Por qué indirecto:** Misma audiencia, mismo contenido, formato diferente (pasivo vs activo)

| Canal | Subs | Nicho | Qué aprender |
|---|---|---|---|
| freeCodeCamp | 9M | Full-stack, Python, AI | Thumbnails, títulos, duración óptima |
| Traversy Media | 2.2M | Web dev, Python | Formato tutorial directo al punto |
| Fireship | 2.5M | Trends tech, shorts | Humor + información en 100s |
| Sentdex | 1.3M | Python, ML | Audiencia española busca equivalente |
| Andrej Karpathy | 800K | AI/LLMs profundo | El estándar de calidad técnica en AI |
| MoureDev (ES) | 700K | Python en español | El referente más cercano a Whetzy en YouTube ES |

**Estrategia Whetzy:** Ser el MoureDev con motor adaptativo. Él enseña, nosotros
enseñamos + el motor personaliza. El CTA de cada video de MoureDev podría ser Whetzy.

### 2.2 GitHub repos de aprendizaje

| Repo | Stars | Relevancia |
|---|---|---|
| `jwasham/coding-interview-university` | 300K+ | Mismo usuario career-switcher |
| `donnemartin/system-design-primer` | 280K+ | Mismo usuario senior |
| `TheAlgorithms/Python` | 190K+ | Contenido [reusar] para Whetzy |
| `EbookFoundation/free-programming-books` | 340K+ | El usuario que busca aquí busca en Whetzy |
| `public-apis/public-apis` | 310K+ | Proyectos prácticos para tracks |

**Estrategia:** Estar presente en los READMEs de estos repos como recurso
complementario. Un PR en `free-programming-books` poniendo Whetzy en la lista
puede generar 10K+ visitas.

### 2.3 freeCodeCamp.org

**Modelo:** 100% gratuito, certificaciones gratuitas, 400M+ visitas/año
**Fortaleza:** La audiencia más grande de aprendizaje de programación del mundo
**Debilidad:** Sin motor adaptativo, sin español nativo de calidad, sin AI Engineering profundo
**Estrategia:** Publicar artículos en freeCodeCamp News (editorial abierta) — acceso
directo a millones de lectores. Un artículo bien escrito puede traer 5,000-50,000 visitantes.

### 2.4 Khan Academy

**Modelo:** 100% gratuito
**Relevancia:** Principiantes absolutos — el usuario que no sabe nada puede llegar
a Whetzy después de Khan Academy
**Estrategia:** Posicionarse como "el siguiente paso después de Khan Academy"
cuando quieres Python para trabajo real.

### 2.5 CS50 (Harvard)

**Modelo:** 100% gratuito, certificado de Harvard al final
**Audiencia:** Millones de principiantes/año
**Estrategia:** CS50 enseña C y Python básico — Whetzy es el lugar donde vas
después de CS50 cuando quieres especializarte en AI Engineering.
Posicionar activamente: "¿Terminaste CS50? Este es tu siguiente paso."

### 2.6 Learn-to-earn con token: Open Campus (EDU Chain), BitDegree y afines — el caso que NO se imita (ADR-33)

**Por qué está aquí:** el dueño propuso un token propio; esta es la evidencia de mercado.

| Caso | Qué fue | Qué pasó | Lección para Whetzy |
|---|---|---|---|
| **Open Campus (EDU, 2023)** | Protocolo educativo con token EDU (Binance Launchpad, abril 2023; respaldado por Animoca), luego «EDU Chain» (L3) con learn-to-earn y credenciales «Open Campus ID» | El token cotiza muy por debajo de sus máximos y el uso real de la plataforma es marginal frente a su capitalización inicial (verificar cifras al citar) | El valor del token no siguió al aprendizaje; siguió al mercado. Lo único reutilizable es la idea de **credencial verificable**, que Whetzy resuelve con Open Badges 3.0 (ADR-37) |
| **BitDegree (BDG, 2017)** | Plataforma de cursos con token de recompensa | El token perdió relevancia; la plataforma sobrevivió como catálogo convencional | Igual que arriba, seis años antes |
| **STEPN / Axie (move/play-to-earn)** | Recompensa con token por actividad | Colapso por reflexividad: precio baja → usuarios mercenarios se van → precio baja más | Los usuarios que vienen por el token se van con el token |
| **Coinbase Earn / Binance Learn & Earn** | Pagan en cripto por ver lecciones | Funcionan | Porque **un exchange paga con dinero real como marketing** y capta clientes de trading. Whetzy no es un exchange |

**Daño específico que solo Whetzy sufriría:** si responder preguntas paga, bots y
farmers responden las 6.233 preguntas con scripts y **envenenan BKT/FSRS/DKT**. El único
activo diferencial se degrada desde dentro. Ver `ECONOMIA.md` §12.

### 2.7 Ecosistema educativo de Solana: Solana Foundation, Superteam, docs oficiales (ADR-38)

**Por qué indirecto y aliado:** la Solana Foundation publica documentación, bootcamps
en YouTube y programas de grants; Superteam (capítulos en México, Argentina, Brasil y
otros) organiza bounties pagados y eventos. Todo en inglés o con traducciones parciales.

**Estrategia:** no competir — **ser el track Solana en español con motor adaptativo**
(track32) y convertir a Superteam en canal (26.8, 27.9) y posible financiación no
dilutiva (H.28). El bounty real de Superteam Earn es el «proyecto final» del track.

**Qué evitar:** cualquier mención a token, airdrop o inversión (ADR-33). Whetzy enseña
la plataforma; no vende exposición a ella.

---

## 3. Tabla resumen de posicionamiento

| | Whetzy | Boot.dev | DataCamp | Platzi | Educative |
|---|---|---|---|---|---|
| Motor adaptativo | ✅ real | ❌ | ✅ parcial | ❌ | ✅ parcial |
| Español nativo | ✅ | ❌ | ❌ | ✅ | ❌ |
| Python→AI Engineer | ✅ | Backend solo | Data solo | General | Parcial |
| Ciberseguridad | ✅ | ❌ | ❌ | ❌ | ❌ |
| Cloud certs | ✅ | ❌ | ❌ | ❌ | ❌ |
| Gamificación | ✅ S24 | ✅✅ | ❌ | ❌ | ❌ |
| B2B ready | ✅ S22 | ❌ | ✅✅ | ✅ | ✅ |
| Marketplace | ✅ S28 | ❌ | ❌ | ❌ | ❌ |
| Créditos cerrados + referidos por activación | ✅ S29 | gemas (sin datos de referidos) | XP (sin datos) | sin datos | ❌ |
| Pago en USDC liquidado en fiat (LATAM) | ✅ tras H.19 | ❌ | ❌ | ❌ | ❌ |
| Credenciales verificables (Open Badges 3.0) | ✅ S29 | ❌ | ❌ | ❌ | ❌ |
| Token / cripto propia | ❌ a propósito (ADR-33) | ❌ | ❌ | ❌ | ❌ |
| Precio base (2026-09-18, **no verificado** salvo Whetzy; ver §A.1) | Pro $14.99 (ADR-41; publicado en la landing, cobro sin abrir) | ~~$49~~ $59/mes · $399/año | $39 | ~~$29~~ $49/mes · $249/año | $20 |
| Empleabilidad | Alta | Alta | Media | Media | Media |

---

## 4. Lo que la Serie 24.0 debe capturar (checklist)

Para cada competidor del §1, navegar el free tier y documentar:

- [ ] Screenshots del flujo de onboarding completo (pasos 1-5)
- [ ] Screenshot del dashboard principal del usuario autenticado
- [ ] Screenshot del sistema de gamificación/racha/logros
- [ ] Screenshot de la página de precios
- [ ] Screenshot de la landing page principal (desktop + mobile)
- [ ] Anotar: tiempo de onboarding hasta primera lección (en segundos)
- [ ] Anotar: qué emoción genera el diseño (confianza / excitación / aburrimiento)
- [ ] Anotar: qué haría Whetzy diferente en esa misma pantalla

Guardar en: `docs/archive/competencia-screenshots-2026-09-19/` (histórico, ADR-48; la captura vigente es §A)
