# Whetzy — Segmentos de Usuario y Personas

> **Documento vivo nº 13.** Define los 6 segmentos con sus personas, pain points,
> propuesta de valor, flujo en la app, métricas de éxito y **créditos/referidos por
> segmento** (`ECONOMIA.md`). Última actualización: 2026-09-18 (sesión bh; ADR-28, ADR-38).

---

## 0. Por qué este documento existe

Una app que sirve a "todos" no sirve bien a nadie. Cada segmento entra por un
dolor diferente, usa la app de forma diferente y paga de forma diferente.
El diseño de la UI (Serie 24), el copy de la landing (Serie 24.2) y la
distribución (Series 26-27) deben hablarle a cada segmento en su idioma.

---

## Segmento 1 — Estudiante / Principiante

### Perfil
- **Edad:** 17-26 años
- **Situación:** Estudiante universitario o recién graduado sin experiencia técnica
- **Contexto LATAM:** México, Argentina, Colombia, España — busca en Google
  "aprender Python gratis", "cómo entrar a tech", "Python para IA"
- **Dispositivo primario:** Móvil (Android, conexión 4G variable)

### Pain points
1. "No sé por dónde empezar — hay miles de cursos y no sé cuál seguir"
2. "Empiezo y abandono — los tutoriales de YouTube no se me quedan"
3. "No tengo dinero para bootcamps o cursos de $200"
4. "Quiero un certificado pero no sé si vale algo"

### Propuesta de valor Whetzy
> "En 10 minutos el motor sabe exactamente dónde estás. No empiezas desde cero
> ni desde donde no llegas — empiezas desde donde puedes avanzar."

### Plan y precio
- **Gratis:** todo el contenido, el motor adaptativo y el repaso espaciado (ADR-41; la propuesta del 2026-09-18 de limitarlo a Python básico no se aplicó nunca)
- **Pro $14.99/mo:** tutor con IA (ADR-45)
- **Gancho de conversión:** Completion del primer módulo → unlock del siguiente = paywall suave

### Flujo en la app
```
Landing → Registro (30s) → Diagnóstico 10 preguntas (3 min)
→ Nivel detectado + track recomendado mostrado visualmente
→ Primera lección (texto + glosario) → Primera sesión adaptativa (5 preguntas)
→ "Completaste tu primer módulo" + racha iniciada
→ CTA Pro al intentar acceder al módulo 2
```

### Métricas de éxito para este segmento
- TTFQ < 120s desde registro
- Day-7 retention > 15%
- Free→Pro conversion > 4% (mejor que benchmark 2.6%)
- Completion rate track01 > 30%

---

## Segmento 2 — Career Switcher

### Perfil
- **Edad:** 25-40 años
- **Situación:** Trabajo actual no técnico (administración, ventas, salud, educación)
  que quiere entrar a tech en 6-12 meses
- **Contexto:** Tiene 1-2 horas/día disponibles, necesita estructura clara
- **Motivación principal:** Salario — developer junior gana 2-3x su sueldo actual

### Pain points
1. "No tengo tiempo para un bootcamp de 12h/semana"
2. "No sé si lo que aprendo me dará trabajo — tengo miedo de perder meses"
3. "He intentado con Udemy y no terminé ningún curso"
4. "No tengo portfolio, no sé cómo demostrarlo a un empleador"

### Propuesta de valor Whetzy
> "Ruta Python→AI Engineer verificada por el mercado laboral. Certificaciones
> que los empleadores reconocen. El motor ajusta el ritmo a tus 2 horas diarias.
> Completion rate > 70% — no eres tú, era el método."

### Plan y precio
- **Pro Max $19.99/mo** (antes «Premium»; lo que añade sobre Pro lo decide el dueño, H.38 / ADR-45)
- **Certificaciones $49/año:** PCEP, AWS CLF, ISC2 CC como primeras credenciales
- **Gancho de conversión:** Ver la "ruta de empleabilidad" completa → solo en Pro Max (propuesta, pendiente de H.38)

### Flujo en la app
```
Landing (sección career-switcher) → "¿Cuánto tiempo tienes por día?"
→ Plan personalizado de 6 meses mostrado → Registro
→ Track 01 (Python básico) acelerado si tiene base
→ Proyectos cada 4 módulos (portfolio building)
→ Simulacro de certificación al final de cada nivel
→ Perfil público compartible con empleadores
```

### Métricas de éxito
- Completion rate > 50% (vs 10-15% industria)
- Certificaciones completadas por usuario > 1 en 6 meses
- Testimonios de empleados conseguidos > 10 en año 1

---

## Segmento 3 — Developer Senior (upskilling a AI)

### Perfil
- **Edad:** 27-45 años
- **Situación:** Developer con 3+ años de experiencia (JS, Java, PHP, .NET)
  que quiere especializarse en IA/ML para acceder a roles AI Engineer
- **Dolor específico:** Ya sabe programar — no quiere repetir fundamentos

### Pain points
1. "DataCamp me pone a hacer print('Hello World') — ya sé programar"
2. "Los cursos de ML asumen que soy data scientist, no developer"
3. "Quiero ir directo a LLMs, RAG, agentes — no a regresión lineal básica"
4. "Necesito las certificaciones de cloud (AWS/GCP) para el cambio de rol"

### Propuesta de valor Whetzy
> "El motor detecta que ya dominas Python en 5 preguntas y te lleva directo
> a LLMs, RAG y arquitecturas de AI. Sin repetir lo que ya sabes."

### Plan y precio
- **Pro $14.99/mo:** Tracks 6-7 (IA/ML/LLMs) + cloud (AWS/Azure/GCP)
- **Bootcamps async $99:** Implementación práctica de sistemas AI en producción
- **Gancho de conversión:** Assessment que demuestra que el motor lo detecta → "impresionante"

### Flujo en la app
```
Landing (sección "Ya sé programar") → Assessment express 15 preguntas
→ "Dominas Python nivel 3/4 — te llevamos directo al track de IA"
→ Skip automático confirmado por BKT → Track 06/07 desde módulo avanzado
→ Proyectos: RAG en 3 días, agente con tool use, fine-tuning
→ Certificaciones cloud asociadas al avance
```

### Métricas de éxito
- Skip rate correcto (BKT confirma nivel) > 90% precisión
- Tiempo hasta primer proyecto IA < 2 semanas
- Conversión a bootcamp async > 10%

---

## Segmento 4 — Profesor / Instructor

### Perfil
- **Quién:** Profesor universitario de informática, instructor de bootcamp,
  developer con experiencia que quiere monetizar conocimiento
- **Situación actual:** Crea contenido en Udemy ($0.10/estudiante), YouTube
  (monetización lenta), o no tiene plataforma
- **Diferenciador clave:** Sus cursos + el motor adaptativo de Whetzy = producto
  mejor que lo que puede crear solo

### Pain points
1. "En Udemy compito contra 10,000 cursos de Python — el mío se pierde"
2. "Creo contenido de calidad pero no tengo distribución"
3. "No tengo tiempo de crear una plataforma propia"
4. "Mis alumnos no terminan los cursos — no es motivador"

### Propuesta de valor Whetzy
> "Tu contenido + nuestro motor adaptativo. Revenue share 80/20 (ADR-45).
> Tus alumnos terminan porque el motor personaliza el camino.
> Tú cobras más porque el producto entrega más."

### Plan y precio
- **Plan Creador 99,99 $/mes (ADR-45)** para publicar; se exige cuando abra el cobro (`CREATOR_PLAN_REQUIRED`)
- **Revenue share:** 80 % creador / 20 % Whetzy por cada venta, tras la comisión del procesador de pagos (ADR-45)
- **Quality gate:** Todo contenido pasa §7 antes de publicarse (garantía de calidad)
- **Incentivo extra:** Instructores top → badge verificado → más visibilidad en marketplace

### Flujo en la app
```
Registro como instructor → Panel de creación de contenido
→ Subir lecciones + preguntas en formato JSON/MD (templates provistos)
→ Quality gate automático (§7): mínimo 15 Q/skill, ≥ 15% exec, glosario
→ Revisión manual si quality gate pasa
→ Publicación en marketplace → Métricas en tiempo real
→ Pago mensual vía Stripe/Paddle (ADR-16)
```

### Métricas de éxito
- Instructores activos año 1: 20+
- Cursos de instructores en catálogo: 50+
- Revenue share pagado mes 12: > $2,000/mes total

---

## Segmento 5 — Empresa / B2B

### Perfil
- **Quién:** CTO, VP Engineering, L&D Manager, HR Tech de empresa con 20-500 empleados
- **Geografía:** LATAM + España + mercado anglófono (ADR-22)
- **Tamaño mínimo de contrato:** 10 seats
- **Decisor:** No es quien aprende — es quien paga

### Pain points
1. "DataCamp cuesta $300/empleado/año y no está en español"
2. "LinkedIn Learning tiene 27,000 cursos pero no sé qué está aprendiendo mi equipo"
3. "El retorno de upskilling es invisible — no tenemos métricas"
4. "Necesitamos subir las habilidades de AI de nuestro equipo antes de Q2"

### Propuesta de valor Whetzy
> "Dashboard de empresa con métricas por empleado. Rutas personalizadas
> por rol (developer, data analyst, security). Certificaciones verificables.
> En español. A $99-199/persona/año — 2-3x más barato que DataCamp."

### Plan y precio
- **Piloto gratuito:** 3 meses, hasta 10 empleados, a cambio de testimonio + datos
- **Plan empresa:** $99/seat/año (10-50 seats), $79/seat/año (50+ seats)
- **Add-ons:** Dashboard avanzado, SSO, integraciones HRIS ($X/mes — HUMAN-BLOCKED)
- **Facturación:** Anual, por transferencia o tarjeta corporativa

### Flujo en la app
```
Demo personalizada (30 min, Calendly) → Contrato piloto gratuito
→ Admin crea empresa → Importa empleados (CSV o invitación)
→ Asigna tracks por rol → Dashboard empresa activo
→ Reports mensuales automatizados al decisor
→ Renovación anual con datos de ROI demostrado
```

### Panel de empresa incluye
- Progreso por empleado (% completado, racha, nivel actual)
- Tiempo invertido por semana
- Certificaciones obtenidas
- Comparativa entre empleados (anónima opcional)
- Exportar CSV para reportes internos

### Métricas de éxito
- Contratos piloto activos mes 3: 3
- Conversión piloto → pago: > 60%
- NDRR (Net Dollar Retention Rate): > 100%
- Contratos activos mes 12: 20 (= $200K ARR solo B2B)

---

## Segmento 6 — Developer Web3 / Solana hispano (ADR-38)

### Perfil
- **Edad:** 20-35 años
- **Situación:** Developer con base en JS o Python (a veces autodidacta) que quiere
  entrar al ecosistema Solana: dApps, programas on-chain, integraciones de pago
- **Contexto:** Superteam tiene capítulos en México, Argentina y Brasil con bounties
  pagados; la documentación oficial está solo en inglés y asume mucho contexto
- **Dispositivo:** Desktop (escribe código); móvil para repasar

### Pain points
1. "La documentación de Solana está en inglés y salta pasos — no sé por dónde empezar"
2. "Rust y Anchor me intimidan; nadie explica el modelo de cuentas desde cero"
3. "Quiero cobrar un bounty de Superteam pero no sé si estoy al nivel"
4. "Los cursos de 'blockchain' son teoría de 2021, no Solana de hoy"

### Propuesta de valor Whetzy
> "El único track Solana en español con motor adaptativo: el modelo de cuentas,
> transacciones, `web3.js` y Anchor hasta resolver tu primer bounty real.
> El motor salta lo que ya sabes de JS o Python."

### Plan y precio
- **Free tier:** módulo 1 de track32 + glosario Solana
- **Pro $14.99/mo:** track32 completo + proyectos (bounties reescritos como ejercicio)
- **Gancho de conversión:** el proyecto final es un bounty real de Superteam Earn

### Flujo en la app
```
Landing (sección Web3 ES/EN) o código `ST-MX`/`ST-AR`/`ST-BR` de un evento Superteam
→ Registro → Diagnóstico (detecta base JS/Python → salta fundamentos)
→ track32: cuentas → transacciones → web3.js en el Worker → Anchor (escenario + decisión)
→ Proyecto = bounty reescrito → Perfil público con bounties resueltos
→ CTA: "Presenta el bounty real en Superteam Earn"
```

### Métricas de éxito
- Usuarios activos en track32 año 1: 200
- Bounties reales resueltos por alumnos (auto-reportados y verificados por URL): 5 en año 1
- Conversión a Pro del segmento: > 5 % (audiencia con mayor intención que la media)

### Qué NO es este segmento
No es un segmento «cripto-inversor» ni recibe token alguno (ADR-33). Es un developer
que aprende una plataforma; los créditos y referidos son los mismos que para los demás.

---

## Resumen de monetización por segmento

| Segmento | Plan | Precio | LTV estimado | % usuarios esperado |
|---|---|---|---|---|
| Estudiante | Free → Pro | $0 → $14.99/mo | $90-180/yr | 60% del total |
| Career Switcher | Pro Max + Certs | $19.99/mo + $49 | $290/yr | 20% |
| Developer Senior | Pro + Bootcamp | $14.99/mo + $99 | $280/yr | 10% |
| Profesor | Revenue share | 30% comisión | N/A | 5% |
| Empresa | B2B seats | $99-199/seat/yr | $990-1,990/empresa | 5% |
| Web3 / Solana | Free → Pro | $0 → $14.99/mo | $180/yr | dentro del 60 % de estudiantes/devs; se mide aparte |

---

## Cómo la app diferencia segmentos

### En el onboarding (3 preguntas)
1. "¿Cuál es tu objetivo principal?" → opciones mapeadas a segmento (incluida «Desarrollar en Solana/Web3» → segmento 6)
2. "¿Cuánto sabes de Python?" → diagnóstico de nivel
3. "¿Tienes 30 min, 1h o 2h+ al día?" → intensidad del plan

El motor detecta el segmento y personaliza:
- El track recomendado
- La velocidad de avance
- El tipo de gamificación (racha vs proyectos vs certificaciones)
- El CTA de upgrade (Pro para estudiante, Pro Max para career-switcher, B2B demo para empresa)

---

## Créditos, referidos y códigos por segmento (ADR-34, ADR-35; spec en `ECONOMIA.md`)

Los créditos no tienen valor monetario, no se transfieren y no se compran
(`ECONOMIA.md` §1). Lo que cambia por segmento es **qué los gana y en qué se gastan**:

| Segmento | Grifo principal | Sumidero principal | Escalera de referidos | Código típico de entrada |
|---|---|---|---|---|
| Estudiante | Racha 7/30 días, módulos completados | Simulacro de certificación (500), congelar racha (150) | 3 activados → 1 mes Pro | `YT-ES-nn`, `TT-ES-nn` (YouTube/TikTok) |
| Career-switcher | Proyectos (200), simulacros aprobados (150) | Informe de dominio PDF (300), bootcamp async (3.000) | 10 activados → certificación oficial (H-BLOCKED por importe; mientras, 6 meses Pro Max) | `LI-ES-nn`, `UNI-<sigla>-<lote>` |
| Developer Senior | Skip confirmado por BKT (50/skill, máx. 500/mes) | Bootcamp async (3.000) | Refiere colegas; pocos, de alto valor | `DEV-<slug>`, `HN-EN` |
| Profesor / Instructor | **No gana créditos** — gana visibilidad (ranking por completion rate de sus alumnos) | — | Su código `PROF-<nombre>-<pct>` da descuento a sus alumnos y atribuye sus ventas | `PROF-…` |
| Empresa | Módulos asignados completados → **bolsa de la empresa** | Seats extra 1 mes (2.000) | — | Lote de un solo uso `EMP-<sigla>-XXXX-XX` para empleados |
| Web3 / Solana | Módulos de track32 | Simulacros, proyectos | Escalera estándar | `ST-MX`, `ST-AR`, `ST-BR`, `ST-EN` (eventos Superteam) |

**Regla de idioma:** un código lleva idioma; el referido aterriza en `/es` o `/en`
según el referente (ADR-17). **Canje solo en web** (Apple 3.1.1); las apps muestran
saldo y recompensas.

**Reactivación (todos los segmentos):** a los 14 días sin entrar, código de 72 h con
200 créditos por email en el idioma del usuario; 1 cada 60 días (29.7).
