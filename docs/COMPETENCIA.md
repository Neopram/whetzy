# Whetzy — Inteligencia Competitiva Exhaustiva

> **Documento vivo nº 14.** Análisis directo + indirecto. Todo verificado en
> free tiers públicos. Ningún dato propietario. Última actualización: 2026-09-18.
> La Serie 24.0 actualizará este doc con screenshots navegados en vivo.

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
| Precio base | $14.99 | $49 | $39 | $29 | $20 |
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

Guardar en: `docs/competencia-screenshots/` (carpeta gitignoreada, solo local)
