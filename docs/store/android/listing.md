# Whetzy — Google Play Store Listing

> Guía de publicación · ledger 23.3 · mismo copy que `docs/store/ios/listing.md` (una sola fuente
> de verdad para la descripción: no se traduce dos veces, se escribe una vez por idioma y se
> reutiliza en ambas tiendas) ajustado a los campos y límites de Play Console · requiere H.3
> (Google Play Console) + 19.3 (Google Play Billing vía RevenueCat) · **precios: solo los de
> ADR-41/49 (Pro 14,99 $ · Pro Max 19,99 $ · Creador 99,99 $ · Certificación 39,99 $ pago único);
> la ficha no publica ninguno hasta que exista el producto de Billing (19.3)**

---

## App details

| Campo | ES | EN |
|---|---|---|
| **Nombre de la app** (30 chars) | Whetzy | Whetzy |
| **Application ID** | app.whetzy | app.whetzy |
| **Categoría** | Educación | Education |
| **Clasificación de contenido** | ⚠️ no es "PEGI 3 / Everyone" — ver nota | ⚠️ not "PEGI 3 / Everyone" — see note |

> **Nota sobre la clasificación de contenido (hallazgo de [S4], revisión legal, 2026-10-03):**
> "PEGI 3 / Everyone" no encaja con el propio producto: el registro exige
> autocertificación de edad ≥13 (`backend/app/models/user.py`,
> `backend/app/api/v1/endpoints/auth.py`), y el plan Creador deja a cualquier
> usuario publicar cursos que otros compran y cursan
> (`instructor_marketplace.py`) — contenido generado por usuarios sin la
> moderación de 19.11 (que solo cubre perfiles y duelos). Google pide declarar
> esto en su propio cuestionario de clasificación de contenido. El valor real
> sale de ese cuestionario, no de esta tabla.

---

## Descripción corta (máx. 80 chars)

**ES:** Aprende a programar en serio — motor adaptativo, 35 tracks, bilingüe
**EN:** Learn to code for real — adaptive engine, 35 tracks, bilingual

---

## Descripción completa (máx. 4.000 chars)

Mismo texto que `docs/store/ios/listing.md` §"Descripción larga" (ES y EN), con un solo cambio:
donde la ficha de iOS dice «RevenueCat + StoreKit», la de Android dice «RevenueCat + Google Play
Billing». El resto — motor adaptativo, código ejecutable, bilingüe nativo, 35 tracks / 730
habilidades, certificaciones — es el mismo producto, así que es el mismo texto. Mantenerlo en un
solo sitio (`ios/listing.md`) y apuntar aquí evita que las dos fichas se desincronicen con el
tiempo, que es justo lo que pasó con los iconos de los tracks (#46: 11 rutas mostraban el nombre
del icono en texto en vez del emoji).

---

## Palabras clave / etiquetas

Play Store no tiene un campo de keywords separado (a diferencia de App Store): el algoritmo de
búsqueda indexa el título y la descripción completa. Por eso la descripción larga repite los
términos de búsqueda más probables de forma natural: Python, AWS, algoritmos, certificaciones, IA,
machine learning — en ambos idiomas, en el cuerpo del texto, no como lista aparte.

---

## URLs

| URL | Valor |
|---|---|
| Sitio web | `https://whetzy.com` |
| Email de soporte | `support@whetzy.com` |
| Política de privacidad | `https://whetzy.com/privacy` |
| Borrado de cuenta | `https://whetzy.com/delete-account` (Play Store lo exige en la ficha, no solo en la app) |

---

## Gráficos requeridos (Play Console)

| Activo | Tamaño | Estado |
|---|---|---|
| Icono de la app | 512×512 px | ✅ `docs/store/icons/android/play-store-512.png` |
| Feature graphic | 1024×500 px | ❌ pendiente — banner promocional de la ficha, no el icono |
| Screenshots de teléfono | 1080×1920 px o superior, mínimo 2 | ❌ pendiente, mismo comando que iOS (ver abajo) |
| Screenshots de tablet 7"/10" | 1200×1920 / 1600×2560 px | recomendado, no obligatorio |

```bash
cd frontend
UI_OUT=../docs/store/screenshots node scripts/ui-snapshots.mjs \
  --only home,tracks,quiz,lesson,stats --lang es,en --vp mobile
```

> Mismo comando y mismas 5 pantallas que `docs/store/ios/listing.md` §"Screenshots requeridos" —
> Play Store acepta los mismos PNG que App Store si cumplen la resolución mínima. Requiere backend
> local corriendo (no lo he ejecutado en esta sesión: el comando necesita el stack completo, no
> solo el backend).

El **feature graphic** (1024×500 px, el banner que aparece arriba de la ficha en Play Store) no
existe todavía en `docs/store/icons/android/` ni en ningún otro sitio del repo — lo busqué con
`find docs/store -iname "*feature*"` y no hay nada. Es un activo gráfico, no texto: queda en
«Fuera de alcance» de este PR (ver el PR).

---

## Notas para el revisor de Google Play

**Cuenta de prueba:**
- Email: `reviewer@whetzy.com`
- Password: (crear antes del envío y actualizar aquí)

**Notas:**
- La app requiere cuenta para acceder al contenido principal (progreso adaptativo por usuario).
- El pago (suscripción) usa RevenueCat + Google Play Billing — no Stripe ni un procesador externo
  dentro de la app (cumple la política de Play de usar el sistema de facturación de Google para
  contenido digital).
- Sin chat ni comentarios entre usuarios. **Sí hay** contenido generado por
  usuarios: el plan Creador deja publicar cursos que otros usuarios compran y
  cursan (`instructor_marketplace.py`, pantallas `InstructorScreen` y
  `MarketplaceScreen`) — corregido el 2026-10-03 tras revisión de [S5] en el
  PR #93; la ficha decía "sin UGC", que no es cierto. El filtro de
  palabras/reportar/bloquear de 19.11 cubre perfiles y duelos, no el
  contenido de los cursos — si Google pide moderación específica para
  cursos, es un punto nuevo a resolver antes de enviar, no algo ya cubierto.
- Las preguntas de código ejecutan Python/SQL en un sandbox WebAssembly local (Pyodide/sql.js),
  sin llamadas externas durante la ejecución — mismo motor que describe `ios/listing.md`.

---

## Permisos de AndroidManifest.xml

Detalle completo y por qué cada uno (o su ausencia) en `docs/store/play-store-data-safety.md` §6.
No se repite aquí para no desincronizar los dos documentos.

---

## IAP — Google Play Billing vía RevenueCat (19.3)

| Product ID | Tipo | Precio (ADR-41/49) |
|---|---|---|
| `app.whetzy.pro.monthly` | Suscripción auto-renovable | $14,99/mes |
| `app.whetzy.promax.monthly` | Suscripción auto-renovable | $19,99/mes |
| `app.whetzy.creator.monthly` | Suscripción auto-renovable | $99,99/mes |
| `app.whetzy.cert.*` | Producto gestionado (pago único) | $39,99 c/u |

> 19.3 (Google Play Billing vía RevenueCat) depende de H.3 (Google Play Console). Sin estos
> productos creados en Play Console, Google rechaza cualquier mención de precios o compras en la
> ficha — mismo motivo que en iOS (`ios/listing.md` §IAP).

---

## Pendiente antes de enviar a revisión

- [ ] H.3 (cuenta de Google Play Console) — solo el dueño
- [ ] 19.3 (productos de Billing configurados en Play Console y RevenueCat)
- [ ] Feature graphic 1024×500 px (diseño gráfico, no texto — fuera de este PR)
- [ ] Screenshots de las 5 pantallas, generados con el comando de arriba
- [ ] Contraseña real de `reviewer@whetzy.com` en este documento
- [ ] Data Safety form de `play-store-data-safety.md` relleno en la consola (no solo en el repo)
