# Whetzy — iOS App Store Listing

> Guía de publicación · actualizado 2026-09-24 (cifras de `check_docs.py`; sin afirmaciones sobre datos reales mientras no haya usuarios, H.10) · requiere H.2 (Apple Developer) + H.14 (macOS) + 17.14 (IAP) · **precios: solo los de ADR-41 (Pro 14,99 $ · Pro Max 19,99 $ · Creador 99,99 $); la ficha no publica ninguno hasta que exista IAP (17.14)**

---

## App metadata

| Campo | ES | EN |
|---|---|---|
| **Nombre de la app** | Whetzy | Whetzy |
| **Subtítulo** (30 chars) | Aprende a programar en serio | Learn to code for real |
| **Bundle ID** | app.whetzy | app.whetzy |
| **SKU** | whetzy-ios-001 | whetzy-ios-001 |
| **Categoría primaria** | Educación | Education |
| **Categoría secundaria** | Productividad | Productivity |
| **Clasificación de contenido** | ⚠️ no es "4+" — ver nota | ⚠️ not "4+" — see note |

> **Nota sobre la clasificación de contenido (hallazgo de [S4], revisión legal, 2026-10-03):**
> "4+" no encaja con el propio producto: el registro exige autocertificación de
> edad ≥13 (`backend/app/models/user.py`, `backend/app/api/v1/endpoints/auth.py`),
> y el plan Creador deja a cualquier usuario publicar cursos que otros compran y
> cursan (`instructor_marketplace.py`) — contenido generado por usuarios sin la
> moderación de 19.11 (que solo cubre perfiles y duelos). Apple trata la
> exposición a UGC no moderado como motivo para subir la clasificación
> (guideline 1.2). El valor real sale del cuestionario de App Store Connect, no
> de esta tabla — quien lo rellene debe responderlo acorde a esto, no poner
> "4+" por defecto.

---

## Descripción corta (30 chars para búsqueda / subtítulo)

**ES:** Aprende a programar en serio  
**EN:** Learn to code for real

---

## Descripción larga (máx. 4.000 chars)

### ES

Whetzy es la academia de programación bilingüe que se adapta a lo que ya sabes — y lo que aún no.

Cubre el camino completo: desde las primeras líneas de Python hasta arquitecturas de microservicios, bases de datos, cloud AWS y modelos de IA. Cada concepto tiene una lección breve y clara, un ejemplo que puedes ejecutar dentro de la app, y preguntas adaptativas que ajustan la dificultad según tu progreso real.

**¿Por qué Whetzy?**
- **Motor adaptativo.** BKT + FSRS deciden qué practicas y cuándo repasas. No adivinamos: lo calculamos.
- **Código que se ejecuta.** Los ejemplos de Python, SQL y JavaScript corren de verdad en la app, sin servidor externo, sin copiar y pegar.
- **Bilingüe nativo.** Todo el contenido está escrito en español e inglés por separado — no es una traducción automática.
- **35 tracks. 730 habilidades.** Python, arquitectura de software, IA/ML, SQL, Linux, algoritmos, redes, ciberseguridad, AWS CLF-C02, SAA-C03, AIF-C01, PCEP, ISC2 CC y más.
- **Sin anuncios. Sin rastreo publicitario de terceros.**

**Cómo funciona**
1. Completa el placement test (5 min) — empezamos donde tú estás, no desde cero.
2. Estudia con lecciones breves (150–300 palabras) y ejecuta el ejemplo directamente.
3. Practica con preguntas adaptativas: el motor elige lo que más te cuesta justo cuando más lo necesitas.
4. Compite en ligas semanales con otros estudiantes.
5. Cuando dominas un módulo, desbloqueas el siguiente.

**Certificaciones**
Prepárate para 11 certificaciones (AWS, Python Institute, ISC2, CompTIA Security+ y Microsoft) con simulacros cronometrados repartidos por los dominios oficiales de cada examen.

### EN

Whetzy is the bilingual coding academy that adapts to what you already know — and what you don't yet.

It covers the full path: from your first lines of Python to microservice architectures, databases, AWS cloud, and AI models. Every concept has a short, clear lesson, a runnable example inside the app, and adaptive questions that adjust difficulty based on your real progress.

**Why Whetzy?**
- **Adaptive engine.** BKT + FSRS decide what you practice and when you review. We don't guess: we calculate it.
- **Code that runs.** Python, SQL and JavaScript examples actually execute inside the app — no external server, no copy-paste.
- **Natively bilingual.** All content is written in Spanish and English separately — not machine-translated.
- **35 tracks. 730 skills.** Python, software architecture, AI/ML, SQL, Linux, algorithms, networking, cybersecurity, AWS CLF-C02, SAA-C03, AIF-C01, PCEP, ISC2 CC, and more.
- **No ads. No third-party ad tracking.**

**How it works**
1. Complete the placement test (5 min) — we start where you are, not from scratch.
2. Study with short lessons (150–300 words) and run the example directly.
3. Practice with adaptive questions: the engine picks what challenges you most, right when you need it.
4. Compete in weekly leagues with other learners.
5. Master a module to unlock the next one.

**Certifications**
Prepare for 11 certifications (AWS, Python Institute, ISC2, CompTIA Security+ and Microsoft) with timed mock exams weighted by each exam's official domains.

---

## Palabras clave (100 chars, separadas por coma, sin espacios)

**ES:** programar,python,aws,aprender,código,algoritmos,cursos,certificaciones,ia,machine learning  
**EN:** coding,python,aws,learn,algorithms,courses,certifications,ai,machine learning,backend

---

## URL de soporte

`https://whetzy.com/privacy`

## URL de marketing

`https://whetzy.com`

## URL de política de privacidad

`https://whetzy.com/privacy`

---

## Screenshots requeridos

| Dispositivo | Tamaño | Mínimo |
|---|---|---|
| iPhone 15 Pro Max (6.7") | 1290×2796 px | 3 |
| iPhone 8 Plus (5.5") | 1242×2208 px | 3 |
| iPad Pro 12.9" (6ª gen) | 2048×2732 px | 3 |

Generar con Playwright (`npm run screenshots:ios`) o manualmente en simulador.

**Pantallas recomendadas para screenshots:**
1. HomeScreen (dashboard con racha y XP)
2. TracksScreen (currículo de un track)
3. QuizScreen (pregunta activa con feedback)
4. LessonScreen (lección con ejemplo ejecutado)
5. StatsScreen (gráfico de progreso)

---

## Notas para el revisor de Apple (Review Notes)

**Cuenta demo:**
- Email: `reviewer@whetzy.com`
- Password: (crear antes del submit y actualizar aquí)

**Notas:**
- La app requiere creación de cuenta para acceder al contenido principal (sistema de progreso adaptativo).
- El pago (suscripción Pro) usa RevenueCat + StoreKit — no Stripe (cumple App Store Review Guideline 3.1.1).
- Sin chat ni comentarios entre usuarios. **Sí hay** contenido generado por
  usuarios: el plan Creador deja publicar cursos que otros usuarios compran y
  cursan (`instructor_marketplace.py`, pantallas `InstructorScreen` y
  `MarketplaceScreen`) — corregido el 2026-10-03 (ver `android/listing.md`,
  misma nota, tras revisión de [S5] en el PR #93). Apple exige moderación de
  UGC (guideline 1.2); el filtro/reportar/bloquear de 19.11 cubre perfiles y
  duelos, no el contenido de los cursos — punto a resolver antes de enviar.
- Las preguntas de código ejecutan Python/SQL en un sandbox WebAssembly local (Pyodide/sql.js), sin llamadas externas durante la ejecución.

---

## Versión de Info.plist requerida

```xml
<key>NSCameraUsageDescription</key>
<string>Whetzy no usa la cámara.</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Whetzy no accede a tus fotos.</string>
<key>NSLocationWhenInUseUsageDescription</key>
<!-- NO incluir: no usamos localización -->
```

> Solo incluir las claves para las APIs que realmente usa la app. Apple rechaza apps con claves vacías para APIs no usadas.

---

## IAP (In-App Purchases) — RevenueCat (17.14)

| Product ID | Tipo | Precio (ADR-41/49) |
|---|---|---|
| `app.whetzy.pro.monthly` | Auto-renovable | $14,99/mes |
| `app.whetzy.promax.monthly` | Auto-renovable | $19,99/mes |
| `app.whetzy.creator.monthly` | Auto-renovable | $99,99/mes |
| `app.whetzy.cert.*` | Consumible (pago único) | $39,99 c/u |

> 17.14 está HUMAN-BLOCKED (H.2 + H.5). Sin estos productos configurados en App Store Connect, Apple rechaza cualquier referencia a compras en la app.
