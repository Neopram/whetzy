# Whetzy — Store Listing (iOS + Android)

> Consolidado de `docs/store/ios/listing.md` y `docs/store/play-store-data-safety.md`.
> Precios: ADR-41/49 (Pro $14,99/mes · Pro Max $19,99/mes · Creador $99,99/mes · Certificación $39,99 pago único).
> Última actualización: septiembre 2026.

---

## 1. Identidad de la app

| Campo | Valor |
|---|---|
| Nombre | Whetzy |
| Bundle ID (iOS) | app.whetzy |
| Application ID (Android) | app.whetzy |
| Categoría primaria | Educación / Education |
| Categoría secundaria | Productividad / Productivity |
| Clasificación de contenido | 4+ (iOS) / Everyone (Android) |
| Idiomas | ES, EN (bilingüe nativo) |

---

## 2. Textos de la ficha

### Descripción corta (≤ 80 chars)

**ES:** Aprende a programar en serio — motor adaptativo, 35 tracks, bilingüe  
**EN:** Learn to code for real — adaptive engine, 35 tracks, bilingual

### Descripción larga

Ver `docs/store/ios/listing.md` §"Descripción larga" — el mismo texto sirve
para ambas tiendas, ajustando la mención de IAP al proveedor correspondiente
(StoreKit en iOS, Google Play Billing en Android).

### Palabras clave (iOS, 100 chars)

**ES:** programar,python,aws,aprender,código,algoritmos,cursos,certificaciones,ia,machine learning  
**EN:** coding,python,aws,learn,algorithms,courses,certifications,ai,machine learning,backend

---

## 3. URLs

| URL | Valor |
|---|---|
| Sitio web | `https://whetzy.com` |
| Soporte | `https://whetzy.com` (email: support@whetzy.com) |
| Política de privacidad | `https://whetzy.com/privacy` |
| Términos de servicio | `https://whetzy.com/terms` |
| Borrado de cuenta | `https://whetzy.com/delete-account` |

---

## 4. Precios e IAP (ADR-41/49)

| Product ID | Tipo | Precio | Notas |
|---|---|---|---|
| `app.whetzy.pro.monthly` | Auto-renovable | $14,99/mes | Pro: quiz ilimitados, sin anuncios |
| `app.whetzy.promax.monthly` | Auto-renovable | $19,99/mes | Pro Max: tutor IA ilimitado + Pro |
| `app.whetzy.creator.monthly` | Auto-renovable | $99,99/mes | Creador: publicar bootcamps |
| `app.whetzy.cert.*` | Consumible (pago único) | $39,99 c/u | Certificación por examen |

> En iOS: StoreKit vía RevenueCat (17.14, H.2). En Android: Google Play Billing vía RevenueCat (19.3, H.3).
> Free tier: sin límite de tiempo, quiz limitados a cupo diario.

---

## 5. Screenshots requeridos

### iOS (App Store Connect)

| Dispositivo | Resolución | Mínimo |
|---|---|---|
| iPhone 15 Pro Max (6,7") | 1290 × 2796 px | 3 |
| iPhone 8 Plus (5,5") | 1242 × 2208 px | 3 |
| iPad Pro 12,9" (6.ª gen) | 2048 × 2732 px | 3 |

### Android (Play Console)

| Tipo | Resolución | Mínimo |
|---|---|---|
| Teléfono | 1080 × 1920 px (o superior) | 2 |
| Tablet 7" | 1200 × 1920 px | recomendado |
| Tablet 10" | 1600 × 2560 px | recomendado |

### Pantallas recomendadas

1. **HomeScreen** — dashboard con racha, XP y progreso
2. **TracksScreen** — currículo de un track con habilidades
3. **QuizScreen** — pregunta activa con feedback
4. **LessonScreen** — lección con ejemplo ejecutable
5. **StatsScreen** — gráfico de progreso

### Generación

```bash
cd frontend
UI_OUT=../docs/store/screenshots node scripts/ui-snapshots.mjs \
  --only home,tracks,quiz,lesson,stats --lang es,en --vp mobile
```

> Requiere backend local corriendo + `npm run dev -- --port 5199`.

---

## 6. Privacidad y datos

Detalle completo en `docs/store/play-store-data-safety.md`.

**Datos recopilados:** email, username (display), quiz performance, subscription status, push token (opcional).  
**Datos NO recopilados:** ubicación, fotos, cámara, contactos, IDFA, salud.  
**Terceros:** Stripe (pagos), Groq (IA — solo texto de preguntas, sin PII), Sentry (opcional, crash logs).  
**Borrado:** `DELETE /api/v1/auth/me/account` + pantalla `/delete-account`.  
**Export:** `GET /api/v1/export/data` (GDPR Art. 20).

---

## 7. Bloqueadores actuales

| Bloqueador | Afecta | Tarea |
|---|---|---|
| H.2 (Apple Developer Program) | iOS submission | 17.14, 19.2 |
| H.3 (Google Play Console) | Android submission | 19.3 |
| H.4 (Stripe live) | Pagos web | — |
| 17.14 (RevenueCat IAP) | App Store 3.1.1 | Requiere H.2 |
| 19.2 (Sign in with Apple) | App Store 4.8 (si hay OAuth) | Requiere H.2 |

---

## 8. Checklist pre-envío

### Ambas tiendas

- [ ] IAP configurado en RevenueCat (17.14)
- [ ] Screenshots de 5 pantallas generados y committeados en `docs/store/screenshots/`
- [ ] Cuenta de revisión creada (`reviewer@whetzy.com`)
- [ ] Privacy policy URL configurada en la consola
- [ ] Borrado de cuenta URL en la ficha (Play Store lo exige)

### iOS adicional

- [ ] Sign in with Apple live (19.2) si existe otro OAuth
- [ ] `PrivacyInfo.xcprivacy` actualizado (ya existe en `docs/store/ios/`)
- [ ] Build firmado subido a App Store Connect

### Android adicional

- [ ] Data Safety form rellenado (ver §6 de `play-store-data-safety.md`)
- [ ] `targetSdkVersion ≥ 35` (ya cumplido)
- [ ] AAB firmado subido a Play Console
