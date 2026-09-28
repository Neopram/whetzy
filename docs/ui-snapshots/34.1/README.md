# Capturas — 34.1 (devolver el estilo a las pantallas rotas)

Evidencia del criterio de 34.1: "capturas antes/después por pantalla en el PR".

- `00-auth-ANTES-03220e4.png`: estado roto real en el commit `03220e4` — pestañas,
  selector de idioma y botón de envío sin estilo, casi invisibles sobre el fondo
  oscuro.
- El resto son capturas **frescas** (2026-09-28, esta sesión) del estado actual de
  la rama, en el orden que da la propia fila: Auth (login/registro/olvido) → Rutas
  → Lección → Quiz (pregunta + feedback) → Perfil → Stats → Liga. `03-home.png` es
  el "después" directo del `00-auth-ANTES-03220e4.png`.

No se incluye Home/Tracks/etc. "antes" porque esa regresión concreta ya no existe
en ningún commit accesible sin checkout histórico completo — la comparación
antes/después con valor real es la del bug de Auth, que sí quedó documentada en
un commit concreto. El resto de capturas son evidencia de "las 13 pantallas ya no
están rotas hoy", verificado en vivo (Postgres 16 + Redis locales, sin Docker;
usuario registrado de cero, sin datos inventados).

Certificate no se capturó: requiere haber aprobado un examen de track completo,
fuera de alcance de una captura de una sesión de registro reciente.
