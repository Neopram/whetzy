# Email a universidades LATAM/España — ledger 26.3

Solo la plantilla. **Sin lista de contactos personales** (regla de esta sesión):
no hay nombres ni correos de personas concretas aquí, solo las instituciones
objetivo que ya estaban públicas en `docs/DISTRIBUCION.md` §9. Encontrar y
confirmar el contacto correcto en cada facultad (nombre, cargo, email) es
trabajo manual del dueño, no algo que se pueda redactar sin inventar datos.

## Instituciones objetivo (ya públicas en `DISTRIBUCION.md` §9 — no son contactos,
son nombres de universidades)

- México: UNAM, IPN, Tec de Monterrey, UDLAP
- Argentina: UBA, UTN, ITBA, Austral
- Colombia: Uniandes, EAFIT, Javeriana
- España: UPM, UAB, UC3M, UPV

15 instituciones, no 50 — `DISTRIBUCION.md` §9 dice "target inicial: 50
universidades" pero solo nombra estas 15. Las 35 restantes no están en el repo
en ningún sitio que haya encontrado (`grep -rn` por nombres de universidad en
`docs/`); inventarlas para completar el número sería justo lo que prohíbe la
línea roja. Si el dueño tiene esa lista en otro sitio, se añade; si no, se
construye a mano — no la genero yo.

## Plantilla ES

**Asunto:** Acceso gratuito a Whetzy para estudiantes de Python/IA — {{Universidad}}

> Hola {{Nombre}},
>
> Soy {{remitente}}, de Whetzy (whetzy.com) — una plataforma adaptativa para
> aprender Python, bases de datos, IA y certificaciones (cloud de AWS y
> Microsoft, ciberseguridad de ISC2). El motor decide qué practicar y cuándo
> repasar según lo que cada
> estudiante ya domina, en vez de un temario fijo igual para todos.
>
> Le escribo porque {{Universidad}} tiene programas de ingeniería/sistemas
> donde esto podría ser útil como complemento gratuito a las clases de Python o
> estructuras de datos. La propuesta es simple: acceso gratuito sin límite de
> tiempo para sus estudiantes durante un semestre, sin coste ni compromiso. A
> cambio, nos interesaría conocer su experiencia de uso — qué funciona y qué no
> — para seguir mejorando el producto.
>
> ¿Tendría 15 minutos para una demo corta? Si prefiere, puedo mandar acceso
> directo para que lo prueben primero sin llamada.
>
> Gracias por su tiempo,
> {{remitente}}
> {{cargo/rol en Whetzy}}

## Plantilla EN (para universidades fuera de habla hispana, si se decide
expandir el alcance — no estaba en el 26.3 original, que es LATAM, pero el
terreno de marketing es bilingüe y la plantilla cuesta lo mismo escribirla ahora)

**Subject:** Free access to Whetzy for Python/AI students — {{University}}

> Hi {{Name}},
>
> I'm {{sender}}, from Whetzy (whetzy.com) — an adaptive platform for learning
> Python, databases, AI, and certifications (AWS and Microsoft cloud, ISC2
> cybersecurity). The engine decides what to practice and when to review based
> on what each student
> already knows, instead of a fixed syllabus for everyone.
>
> I'm reaching out because {{University}} has engineering/CS programs where
> this could be a useful free complement to Python or data structures courses.
> The offer is simple: free, unlimited-time access for your students for one
> semester, no cost, no commitment. In exchange, we'd value hearing how it goes
> — what works and what doesn't — to keep improving the product.
>
> Would you have 15 minutes for a short demo? Happy to send direct access first
> if you'd rather try it before a call.
>
> Thanks for your time,
> {{sender}}
> {{role at Whetzy}}

## Qué pedir a cambio, explícito (para que quien envíe el correo no improvise
en la llamada)

- Feedback real de uso (qué frena, qué les gustó) — no un testimonio pulido de
  marketing; si luego se cita algo que digan, cita exacta, con su nombre y
  permiso expreso, nunca parafraseado como si fuera una frase suya.
- Datos de uso agregados del grupo (cuántos entraron, cuántos volvieron) si la
  universidad quiere compartirlos — no se pide acceso a datos de estudiantes
  individuales.
- Co-branding opcional (mención en su web de recursos complementarios) — nunca
  presentado como "partnership oficial" o "alianza" sin que exista un acuerdo
  firmado.

## Seguimiento si no responden

Un único recordatorio a los 10 días, mismo asunto con "(seguimiento)" al final.
Si no hay respuesta al segundo intento, no insistir — pasar a la siguiente
institución de la lista.
