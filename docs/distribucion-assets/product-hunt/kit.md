# Product Hunt — kit de lanzamiento (ledger 27.4)

Preparación y redacción. Publicar (crear la cuenta de maker, enviar el post, el
día del lanzamiento en sí) es H.23/"Solo el dueño" — lanzamiento real está además
`HUMAN-BLOCKED` en la fila 27.5 del ledger. Nada de esto se envía desde aquí.

## Tagline (ya fijado en `docs/DISTRIBUCION.md` §7 — se repite aquí para no
desincronizar dos fuentes)

**EN:** "The adaptive Python→AI learning platform that learns how you learn"
**ES:** "La plataforma que adapta el camino a cómo tú aprendes Python para IA"

## Cuándo lanzar (criterio ya fijado en `DISTRIBUCION.md` §7, no decido uno nuevo)

> "Día siguiente a que Serie 24 esté DONE y los 4 guardias ADR-18 pasen."

No he comprobado el estado actual de la Serie 24 ni de los 4 guardias de ADR-18
en esta sesión — es una condición de arranque que depende de otras series, fuera
de mi terreno. Si alguien necesita saberlo antes de fijar fecha: `python
scripts/ledger.py series 24` y `grep -n "ADR-18" docs/DECISIONS.md`.

## Categoría

Education + Developer Tools (ya fijado en `DISTRIBUCION.md` §7).

## Primer comentario del maker (se publica junto con el post, mismo tono que
el "first comment" de Show HN — PH también premia que el fundador explique el
porqué, no solo el qué)

> Hey PH! I'm the solo builder behind Whetzy. I built this because I kept seeing
> the same gap: adaptive learning (the kind that tracks what you actually know
> and schedules reviews so you don't forget it — BKT + FSRS under the hood, not
> just "video course + quiz") barely exists for programming, and when it does,
> it's English-only. 500M+ Spanish speakers get a translated afterthought at
> best.
>
> Whetzy is bilingual from the ground up — not machine-translated, written
> natively in both languages — and code examples (Python, SQL, JS) run right in
> the browser via WebAssembly, so you're never copy-pasting into an external
> sandbox. No daily quiz cap on the free tier today, no credit card needed.
>
> Would love PH's take on what's missing from "serious" coding education, and
> where this breaks if you push on it. I'll be around all day to answer
> anything — the engine, the content pipeline, or what it's like building this
> solo.

## Qué necesita el dueño antes de poder lanzar (no redactable, son personas o
cuentas reales)

- **Lista de 100 "upvoters" confirmados** (personas reales que se comprometen a
  votar el día del lanzamiento): esto no lo puedo redactar — serían identidades
  inventadas, justo lo que prohíbe la línea roja (ningún testimonio ni dato de
  persona fabricado). Es una lista de contactos reales del dueño (red personal,
  comunidades donde ya tiene presencia) — queda en "Solo el dueño".
- **Cuenta de maker en Product Hunt**, creada y con historial propio — un perfil
  nuevo sin actividad previa lanzando el mismo día no ayuda al ranking (mismo
  principio que en Show HN).
- **Demo video de 2 minutos**: activo audiovisual, no texto — fuera de este PR
  (ver "Fuera de alcance" del PR).

## Assets de imagen pendientes (gráficos, no texto — mismo motivo que el
"feature graphic" de la ficha de Android en `docs/store/android/listing.md`)

- [ ] 5 screenshots para la galería del post (mismo comando y mismas 5 pantallas
      que `docs/store/ios/listing.md` §"Screenshots requeridos": Home, Tracks,
      Quiz, Lesson, Stats)
- [ ] Thumbnail/gallery image principal (240×240 px mínimo que pide PH)
- [ ] Demo video de 2 min (mencionado arriba)

## Checklist de lanzamiento (el día en sí, para quien lo ejecute)

- [ ] Publicar a las 00:01 PT (hora de PH para que el día de ranking cuente completo)
- [ ] El maker responde cada comentario en las primeras 3 horas
- [ ] Nada de pedir upvotes de forma coordinada en redes el mismo momento del
      lanzamiento (Product Hunt penaliza picos de voto no orgánicos, igual que HN)
- [ ] Ningún número en los comentarios del día que no esté ya citado en este repo
- [ ] Antes de publicar: reconfirmar `FREE_DAILY_QUOTA_ENABLED` en producción (hoy
      `False` por defecto, `backend/app/core/config.py:244` — "no daily cap" en el
      primer comentario deja de ser cierto si alguien lo activa antes del lanzamiento)
