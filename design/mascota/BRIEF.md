# Mascota de Whetzy — brief para el ilustrador

Fila 46.8 (`docs/PLAN_UI_AVANZADA.md` §6, ADR-67 D2). El dueño decidió el 2026-10-19 que haya mascota, y que la
dibuje **una persona**: lo que hace una IA no es exclusivo y no se puede registrar como marca
(`design/iconos/PROCEDENCIA.md`). Las tres láminas de esta carpeta (`direccion-{a,b,c}.svg` y sus PNG) son **bocetos
de dirección hechos por IA** para orientar el encargo; no son la mascota ni se entregan como tal.

## Quién es Whetzy

App para preparar certificaciones técnicas (AWS, seguridad, Python…) con repaso espaciado y preparación por dominio
del examen. «Whet» es afilar: el producto afila lo que ya sabes. La guía de diseño (`design/v2/GUIA.md`) pide una
personalidad **precisa, tranquila, honesta y técnica**, sin confeti ni urgencias falsas.

La mascota acompaña sin distraer. No es un personaje de dibujos animados ni compite con el código que el alumno está
leyendo.

## Direcciones (bocetos IA, para elegir o mezclar)

| | Idea | Por qué |
|---|---|---|
| A · Piedra | Una piedra de afilar con un filo de luz cian | Es el nombre del producto; sólida, tranquila |
| B · Chispa | La chispa que salta al afilar, con el degradado del logo | Más expresiva; enlaza con el símbolo de la marca |
| C · Cursor | El cursor de una terminal, que parpadea cuando piensa | Técnico y sobrio; muy legible en tamaño pequeño |

Fuera: búhos y animales con plumas (Duolingo), personajes redondos tipo peluche (Mimo), cualquier parecido con
mascotas de la competencia o con el logo de otra marca.

## Dónde sale y a qué tamaño

| Momento | Tamaño | Duración de la animación | Nivel (§6.0) |
|---|---|---|---|
| Tarjeta de respuesta del quiz (acierto o fallo), esquina superior derecha | 36 px | ≤ 400 ms | 1 |
| Hoy: una habilidad sube de banda; asoma por la esquina de la celda | 48 px | 600 ms | 2 |
| Ceremonia: sube de nivel, insignia nueva, racha 7/30/100 | 72–120 px | ≤ 3 s, se puede saltar | 4 |
| Estado quieto (primer fotograma de cada animación) | todos | — | — |

Tiene que leerse a **36 px**: siluetas simples, pocos detalles, grosor de línea que no desaparezca.

## Poses

Neutral, acierto, fallo y celebración, como en las láminas. El **fallo es pensativo, no triste**: equivocarse es parte
de aprender y no se castiga. La celebración es contenida: un gesto, no fuegos artificiales.

## Color y temas

- Paleta de la marca (`design/brand/README.md`): fondo `#0A0E1A`, acento `#00BFFF`, degradado
  `#00BFFF → #7B68EE → #C71585 → #FF1493`.
- La app tiene **tema oscuro y claro**. La mascota tiene que verse bien sobre los dos: o una versión por tema, o un
  contorno que funcione en ambos.
- Sin texto dentro de la mascota (la app es ES/EN).

## Animación

- **Lottie** (JSON de bodymovin), que ya está en el bundle. **No Rive**.
- Un archivo por animación: acierto, fallo, asomarse, celebración, y un parpadeo de espera opcional.
- Peso orientativo: ≤ 30 KB por JSON. Sin imágenes incrustadas: solo formas vectoriales.
- El **primer fotograma** de cada una tiene que servir como imagen quieta: con «reducir movimiento» la app no anima y
  enseña ese fotograma.

## Accesibilidad

La mascota es decorativa: la app la marca `aria-hidden` y el texto de la pantalla dice lo mismo («¡Correcto!»,
«Nueva insignia: …»). Por eso no puede ser lo único que comunica algo.

## Entregables

1. SVG por pose, con capas con nombre (cuerpo, ojos, efectos), en los dos temas si hacen falta.
2. Los JSON de Lottie y los ficheros fuente (After Effects u otro).
3. Una hoja de uso de una página: tamaños mínimos, márgenes, qué no hacer.

## Derechos (condición del encargo)

- **Obra original** de la persona que la dibuja, **sin herramientas de IA generativa** en el dibujo ni en la
  animación: es lo que la hace registrable como marca.
- **Cesión total** al dueño de Whetzy de los derechos de explotación (todos los usos, territorios y medios), con
  derecho a modificarla y a registrarla como marca.
- Garantía de que no copia ni deriva de obras de terceros.

## Cómo entra en la app

Cuando el dueño tenga el diseño final, una fila nueva lo integra: 46.1 (tarjeta del quiz), 46.3 (Hoy) y 46.7
(ceremonias), con capturas para que el dueño las apruebe antes de fusionar. Hasta entonces la app sigue con el icono
de la racha y el check.
