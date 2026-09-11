# Whetzy — Estrategia Definitiva v3
## De plataforma a infraestructura educativa adaptativa
*Federico Galindez Castillo | 8 de septiembre de 2026*

---

## Qué cambia en v3

v2 definía qué construir y cómo aprender dentro de Whetzy. v3 abre el sistema hacia afuera: cualquier experto puede construir un bootcamp sobre el motor de Whetzy, cobrarlo, y ser remunerado por sus resultados — no solo por sus ventas. Eso convierte a Whetzy en infraestructura, no en producto.

---

## Parte I — El cambio de categoría

### La diferencia entre app e infraestructura

| App de aprendizaje | Infraestructura educativa |
|-------------------|--------------------------|
| Compite con Duolingo, DataCamp | Se convierte en el motor que otros usan |
| Crece con el equipo de Federico | Crece con cada creador que se une |
| Limitada por el tiempo de un humano | Escala sin límite humano |
| Muere si el contenido se queda viejo | Se actualiza sola porque los creadores compiten |
| Valoración: múltiplo de ingresos | Valoración: múltiplo de marketplace (3–5× mayor) |

Shopify vale más que cualquier tienda que corre sobre Shopify. Stripe vale más que cualquier negocio que usa Stripe. Whetzy como infraestructura vale más que cualquier bootcamp que corre sobre Whetzy.

### La tesis en una frase

Whetzy es el motor adaptativo que convierte el conocimiento de cualquier experto en un bootcamp que certifica resultados reales — y los remunera por esos resultados.

---

## Parte II — Certificaciones por track

### La decisión

Cada track de aprendizaje propio de Whetzy termina con preparación específica para la certificación oficial que el mercado ya reconoce — no una certificación propia de Whetzy (que no vale nada todavía).

| Track Whetzy | Certificación objetivo | Por qué |
|-------------|----------------------|---------|
| 01 Python Básico | PCEP — Python Certified Entry | Python Institute, reconocida globalmente |
| 02 Python Intermedio | PCAP — Python Certified Associate | Escalón natural |
| 03 Python Avanzado | PCPP — Python Certified Professional | Techo de Python puro |
| 04 Ingeniería de Software | PSM I + GitHub Actions cert | Scrum + CI/CD |
| 05 Arquitectura de Software | TOGAF Foundation | Enterprise, reconocida globalmente |
| 06 Fundamentos de IA | TensorFlow Developer Certificate | Google, reconocida por empleadores |
| 07 Ingeniería de IA | AWS Machine Learning Specialty | El más respetado en ML engineering |
| 08 Cybersecurity | Security+ SY0-701 | 48% de job postings cyber |

### Cómo funciona el alineamiento

El track NO reemplaza a la certificación. La hace alcanzable.

```
Track 01 (Python Básico) termina:
  → Boss battle del track (Whetzy)
  → Medidor Beta-binomial: "P(PCEP) = 91%"
  → Simulacro PCEP: 40 preguntas, formato real
  → "Estás listo. El examen cuesta $59."
  → Link a Python Institute (comisión de afiliado 10–15%)
```

El usuario paga a Whetzy para aprender. Paga a Python Institute para certificarse. Whetzy gana comisión de afiliado además de la suscripción.

### Programas de afiliados a verificar y activar

- Python Institute (PCEP, PCAP, PCPP): comisión estimada 10–15% [Guessing — verificar antes de publicar]
- CompTIA (Security+, Network+): ~10% [Guessing — verificar]
- Microsoft Learn Marketplace: partners registrados
- ISC2 (CISSP): programa de referidos

Acción: contactar Python Institute y CompTIA antes del lanzamiento de cada track. Son gratuitos de activar.

---

## Parte III — El Marketplace de Creadores

### La decisión

Cualquier usuario verificado con BKT ≥ 0.85 en los skills de su dominio puede solicitar ser Creador y publicar bootcamps en Whetzy.

Split: **70% creador / 30% Whetzy**.

### Los tres tipos de creador

**Tipo A — Experto individual**
Un profesional de cybersecurity, un data engineer de Google, un arquitecto de AWS. Publica un bootcamp de su especialidad.

**Tipo B — Institución educativa**
Un bootcamp, una universidad, una empresa de capacitación. Usa Whetzy como plataforma para sus cursos.

**Tipo C — Empresa**
Onboarding técnico estandarizado para empleados. Bootcamps privados internos.

### El modelo de ingresos del creador — tres fuentes

**Fuente 1 — Ventas directas (70%)**
Cada compra de su bootcamp: el creador recibe el 70%.

**Fuente 2 — Comisión por tasa de aprobación**
Si la tasa de aprobación del bootcamp en el examen oficial supera el benchmark:
- ≥ 70% de aprobación → bonus del 5% sobre ventas del mes
- ≥ 80% → bonus del 10%
- ≥ 90% → bonus del 15% + badge "Certified Instructor"

Esta es la innovación central. Hoy en Udemy un instructor cobra cuando vende — el incentivo es el marketing, no la calidad. En Whetzy el instructor cobra más cuando sus estudiantes aprueban el examen oficial. Los incentivos están completamente alineados con el resultado del estudiante. Ninguna plataforma educativa hace esto. Es posible solo porque Whetzy tiene el medidor Beta-binomial y datos de aprobación reales.

**Fuente 3 — Royalty por uso institucional (60%)**
Si una institución compra licencias del bootcamp del creador para sus estudiantes: 60% al creador (vs 70% en venta directa), 40% a Whetzy por la gestión institucional.

---

## Parte IV — Arquitectura del Creator Hub

### El flujo completo del creador

**Paso 1 — Verificación (automática, 1–3 días)**
- BKT ≥ 0.85 en los skills del dominio a enseñar
- Al menos 100 respuestas en el track relevante
- Cuenta verificada con email y nombre real

Si no cumple BKT: "Completa el track de Cybersecurity con dominio ≥ 85% para enseñarlo." La barrera técnica verifica que quien enseña sabe lo que enseña. Ningún otro marketplace hace esto.

**Paso 2 — Creator Studio (sin código)**
- Editor visual de módulos y skills
- Subida de preguntas en JSON, CSV, o editor inline
- O el Agente de Contenido: "Genera 50 preguntas sobre Docker avanzado con fuentes verificadas" → agente genera → creador revisa → publica
- Definición de prerequisitos, precio, certificación objetivo
- Activación del medidor Beta-binomial

**Paso 3 — QA automático antes de publicar**
El agente QA revisa:
- Esquema válido
- Fuente canónica en ≥ 80% de preguntas
- Sin duplicados en el banco global
- Distribución equilibrada de dificultad (Elo)
- Cobertura de todos los dominios del examen oficial

Marca issues con corrección sugerida. El creador aprueba o rechaza cada corrección.

**Paso 4 — Publicación y descubrimiento**
El bootcamp aparece en el catálogo por tema, certificación, tasa de aprobación, idioma, nivel y precio. La recomendación personalizada usa BKT del usuario: "Basado en tu dominio de Python Avanzado, este bootcamp de FastAPI tiene un 94% de match contigo."

**Paso 5 — Analytics del creador**
- Usuarios activos, completación, abandono por módulo
- Pregunta con más fallos (la que más necesita revisión)
- Tasa de aprobación en examen oficial (reportada por usuarios)
- Ingresos del mes, acumulados, bonus pendiente
- Comparación anónima vs media del dominio

### La guía personalizada que Whetzy genera al creador

Cuando empieza, Whetzy genera una guía para su dominio específico desde los exam guides oficiales:

```
GUÍA PARA TU BOOTCAMP: "AWS SAA — De Zero a Certified"

Estructura basada en SAA-C03 Exam Guide oficial:
  Dominio 1: Design Secure Architectures (30%)
    → Módulos: IAM, KMS, Security Groups, NACL
    → Preguntas mínimas: 90
    → Distribución Elo: 30% fácil, 50% medio, 20% difícil
  
  Dominio 2: Design Resilient Architectures (26%)
    → Módulos: Multi-AZ, Auto Scaling, ELB, Route 53
    → Preguntas mínimas: 78
  
  [... todos los dominios ...]

Fuentes canónicas verificadas:
  → AWS SAA-C03 Exam Guide (oficial, público)
  → AWS Well-Architected Framework (público)
  → AWS Documentation (pública)

El Agente de Contenido puede generar el primer draft
desde estas fuentes. ¿Empezar con el Dominio 1?
```

El creador no necesita saber pedagogía. La guía le dice exactamente cuántas preguntas, qué distribución, qué fuentes, y qué cobertura necesita para que el medidor sea estadísticamente válido.

---

## Parte V — Modelo institucional

### Los cuatro segmentos

**Bootcamps y academias técnicas — $299–$999/mes**
Tienen contenido pero no motor adaptativo. Reciben su catálogo de cursos sobre el motor de Whetzy con analytics de estudiantes, tasa de aprobación por módulo, y reportes para acreditación.

**Universidades — $1,000–$5,000/mes**
Necesitan demostrar resultados y acreditación. Reciben plataforma white-label opcional, integración con LMS (Canvas, Moodle), reportes SCORM, medidor Beta-binomial por materia.

**Empresas — $500–$3,000/mes**
Onboarding técnico caro y lento. Reciben bootcamps privados, dashboards de progreso por empleado, alertas de riesgo (churn prediction = empleado en riesgo de abandonar el programa), certificaciones internas verificables.

**Colegios STEM — $99–$299/mes por aula**
Un profesor, 30 estudiantes de niveles distintos — diferenciación imposible manualmente. El motor adaptativo la hace automáticamente. El profesor ve un dashboard de la clase: qué sabe cada estudiante, quién necesita ayuda, y cuál es el concepto más débil del grupo.

### El panel del profesor

```
DASHBOARD DE AULA — Grupo Python Avanzado (28 alumnos)

Media de dominio: 58%
  Avanzados (BKT > 0.8): 6 alumnos
  En progreso (0.5–0.8): 14 alumnos
  En riesgo (< 0.5): 8 alumnos ← Acción recomendada

Skills más débiles del grupo:
  1. Decoradores avanzados (media 0.31)
  2. Context managers (media 0.38)
  3. Metaclases (media 0.29)

Alumnos en riesgo de abandono:
  → Ana M.: 6 días sin acceso, BKT bajando en 3 skills
  → Carlos R.: tiempo de respuesta +60%, posible fatiga

Recomendación para la próxima sesión presencial:
  20 min en Decoradores avanzados — mayor brecha del grupo.
  El motor ya los preparó individualmente; la sesión puede
  ir directo al concepto difícil.

[Enviar recordatorio a alumnos en riesgo]
[Generar reporte para acreditación]
[Ver detalle por alumno]
```

Esto es lo que ningún LMS ofrece. Moodle y Canvas muestran quién entregó qué. Whetzy muestra qué sabe cada estudiante, qué está a punto de olvidar, y quién está en riesgo de abandonar — con datos del motor.

---

## Parte VI — Modelo de monetización completo

### Todos los flujos de ingreso

```
B2C INDIVIDUAL
  Free: 2 tracks básicos, 20 preguntas/día
  Pro $9.99/mes: todos los tracks de aprendizaje
  Pro+ $19.99/mes: Pro + todas las certs
  Track unlock $14.99: acceso perpetuo a 1 track
  Cert unlock $29.99: acceso perpetuo a 1 cert
  Comisiones afiliado (Python Institute, CompTIA): 10–15%

MARKETPLACE (30% de cada transacción de creadores)
  Bootcamps de creadores externos

B2B INSTITUCIONAL
  Bootcamps: $299–$999/mes
  Universidades: $1,000–$5,000/mes
  Empresas: $500–$3,000/mes
  Colegios STEM: $99–$299/mes por aula
  Setup fee: €2,000–€5,000

CREATOR PRO $49.99/mes
  Analytics avanzados, dominio personalizado,
  certificados con su marca, agente de contenido sin límite,
  webhooks, soporte prioritario
```

### Proyección con marketplace activo

Con 5,000 usuarios + 50 creadores activos + 10 clientes B2B:

```
B2C suscripciones:          ~$29,000
Marketplace (30%):           ~$7,500
B2B institucional:           ~$11,500
Creator Pro (20 × $49.99):   ~$1,000
Comisiones afiliado:         ~$2,000

BRUTO:                      ~$51,000
- Costos operativos:         -$3,000
- Comisiones tiendas:        -$5,800
NETO:                       ~$42,200/mes
```

El marketplace multiplica el ingreso sin multiplicar el trabajo. Cada creador que publica un bootcamp trae su propia audiencia a Whetzy.

---

## Parte VII — Protección de calidad del marketplace

El mayor riesgo es que el marketplace se llene de bootcamps malos que destruyan la reputación de Whetzy. Tres capas:

**Capa 1 — Barrera de entrada técnica (BKT)**
Para crear un bootcamp de Cybersecurity, necesitas BKT ≥ 0.85 en ese dominio. Elimina a quienes no saben lo que pretenden enseñar. Ningún otro marketplace hace esto.

**Capa 2 — QA automático antes de publicar**
El agente QA revisa cada pregunta. Rechaza sin fuente, con respuestas incorrectas, con cobertura insuficiente. El creador corrige antes de que llegue a un estudiante.

**Capa 3 — Reputación basada en resultados**
Tasa de aprobación pública. Bootcamps < 50% marcados con advertencia. < 30% tras 90 días → revisión obligatoria. ≥ 80% → badge "Top Instructor" + prioridad en el marketplace.

El sistema se auto-regula: el creador con contenido malo pierde visibilidad y bonus. El creador con contenido bueno gana más dinero. Sin equipo de moderación humano.

---

## Parte VIII — El efecto de red defensible

```
Más creadores → más bootcamps → más variedad
      ↓
Más variedad → más usuarios
      ↓
Más usuarios → más datos de aprobación reales
      ↓
Datos reales → medidor Beta-binomial más preciso
      ↓
Medidor preciso → garantía de aprobación más creíble
      ↓
Garantía creíble → más creadores quieren publicar
      (sus bootcamps venden más con garantía)
```

Un competidor puede copiar el motor. No puede copiar los datos de aprobación de 10,000 estudiantes en 50 certificaciones ni la red de 200 creadores verificados. Ese es el foso.

---

## Parte IX — Scorecard v3

| Dominio | Hoy | Con v3 |
|---------|-----|--------|
| Motor adaptativo | 5 | 5 |
| Ciencia del aprendizaje | 2 | 5 |
| Volumen de contenido | 2 | 5 |
| Material de lectura | 1 | 5 |
| Práctica de código | 1 | 5 |
| Cybersecurity | 0 | 5 |
| Certificaciones por track | 0 | 5 |
| Visualización del progreso | 1 | 5 |
| Gamificación | 4 | 5 |
| Bilingüe | 5 | 5 |
| Diseño/UX | 4 | 5 |
| Comunidad | 2 | 5 |
| Precio/valor | 4 | 5 |
| Escalabilidad del contenido | 0 | 5 |
| Modelo institucional | 0 | 5 |
| Marketplace de creadores | 0 | 5 |
| **Promedio** | **2.1** | **5.0** |

---

## Parte X — Orden de ejecución v3

### Inmediato — humano
1. Registro autónomo griego
2. Google Play Console ($25)
3. Contactar Python Institute y CompTIA para afiliados

### Semanas 1–2 — lógica sobre el motor existente
4. Stripe: checkout + webhook + entitlements
5. Calibración de confianza (Seguro/Dudo/Adivino)
6. Tipificación de errores + remediación por tipo
7. Reaprendizaje 3×3 + indicador visual
8. "Dominado" estricto (5 condiciones)
9. Modos de quiz + fatiga + cierre de sesión
10. Registro de distractor → matriz de confusión

### Semanas 3–4 — contenido + navegación
11. Navegación hub: 4 tabs, barra de contexto, Continuar
12. Track 08 Cybersecurity: 800 preguntas (sesiones autónomas)
13. Cert Security+: 400 preguntas + badges probabilidad + Beta-binomial
14. Pyodide: sandbox hardening + validación server-side
15. Build Android + publicación Google Play

### Semanas 5–8 — lecciones + Mapa + Creator Studio v1
16. Lecciones 5 capas para 207 skills (sesiones autónomas)
17. Mapa v1: terreno + clima + avatar + estela + tocar zona
18. Creator Studio v1: solicitud + verificación BKT + QA automático
19. Agente de contenido para creadores
20. Primer creador invitado (beta privada)
21. Medidor Beta-binomial para Security+
22. Glosario a 500 términos con páginas públicas
23. Boss battles + cofres + combos
24. Contenido en redes: 3 videos/semana

### Semanas 9–12 — Mapa v2 + certs + Apple + marketplace público
25. Mapa v2: predicción, zoom, capas pintadas, deep links
26. Ajuste personal FSRS
27. Cert CISSP + AWS CP + AWS SAA
28. Alineamiento cert por track (PCEP, PCAP)
29. Marketplace público (10+ bootcamps verificados)
30. Dashboard del creador con tasa de aprobación + bonus
31. Clanes de estudio
32. App Store de Apple

### Meses 4–6 — institucional
33. Panel del profesor/administrador institucional
34. Primer cliente B2B institucional
35. Creator Pro ($49.99/mes)
36. Tracks 02–05 a 400 preguntas
37. Certs AI-102 + Google ML
38. Proyectos guiados por track
39. Glosario a 1,000 términos
40. Outreach a YouTubers con métricas reales

### Meses 7–12 — defensibilidad
41. Integración TryHackMe/HackTheBox
42. Garantía de aprobación activa
43. Mentoría entre pares
44. Modelo colegios STEM
45. Portugués brasileño
46. Transparencia del motor
47. Cuenta en inglés

---

## Parte XI — Lo que no se hace

- No microservicios hasta 50,000 usuarios
- No Kubernetes hasta que Railway no alcance
- No DKT en producción hasta AUC > 0.70
- No voz ni OCR
- No certificación propia de Whetzy en fase 1
- No marketplace abierto sin verificación BKT
- No inversión externa hasta €10K MRR
- No cuenta en inglés hasta 5,000 seguidores en español
- No Apple hasta que Google Play valide D7 > 40%

---

## Resumen ejecutivo

Whetzy empieza como la mejor plataforma de aprendizaje técnico adaptativa en español. Termina como la infraestructura educativa sobre la que expertos, bootcamps, universidades y empresas construyen sus programas de formación.

El cambio de categoría no requiere reinventar nada. El motor que ya existe es exactamente lo que las instituciones educativas necesitan y no tienen. El Creator Hub convierte ese motor en un servicio que cualquier experto puede usar sin saber programar.

La comisión por tasa de aprobación es la innovación que ningún marketplace educativo ha hecho. Alinea completamente el incentivo del creador con el resultado del estudiante. Hace que la garantía de aprobación sea sostenible. Y genera un efecto de red que se defiende solo: los datos de aprobación de miles de estudiantes + la red de creadores verificados no se copia en semanas.

El foso no es el código. Es la confianza acumulada, medida en resultados reales.

---

*Documento elaborado en conversación con Claude (Anthropic) | 8 de septiembre de 2026*
*Todos los derechos sobre Whetzy, su código, contenido, marca, arquitectura y estrategia pertenecen a Federico Galindez Castillo*
