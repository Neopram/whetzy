# Whetzy — Store Listing (iOS + Android)

> Resumen de las dos tiendas. El detalle vive en `docs/store/ios/listing.md` (notas para Apple, Info.plist, IAP) y `docs/store/play-store-data-safety.md` (formulario Data Safety); si divergen, manda el detalle.
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
| Clasificación de contenido | No es 4+ / Everyone: ver la nota en `store/ios/listing.md` y `store/android/listing.md` |
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

**RevenueCat: lo comprobado el 2026-10-20 (D.3; pendiente de decisión del dueño, sin código).**

- **Precio.** Plan Pro gratis hasta 2.500 $ de ingresos mensuales registrados (MTR); por encima, el 1 % de lo
  registrado. Fuentes: <https://www.revenuecat.com/plans/> («Pay nothing for up to $2,500 in monthly tracked
  revenue») y <https://www.revenuecat.com/docs/welcome/set-up-revenuecat/account-management> («beyond that limit …
  we will bill for 1% of MTR»). Ninguna de las dos páginas lleva fecha. Un artículo suyo sobre un plan antiguo
  habla de 10.000 $: es el plan heredado de cuentas viejas, no el actual.
- **Probar sin las consolas de pago.** Cada proyecto trae una *Test Store*: «No platform accounts needed - Test
  without App Store Connect or Google Play Console access»
  (<https://www.revenuecat.com/docs/test-and-launch/sandbox>, sin fecha). La compra abre un diálogo de prueba
  (éxito, fallo, cancelar), concede el *entitlement* y llega al panel, sin pasar por Apple ni Google. Se usa
  con una clave de API propia de la Test Store que **nunca** debe ir en una build de tienda («never Test Store
  API key!», misma página). No simula renovaciones reales, precios por región ni la revisión de la tienda.
- **SDK.** `@revenuecat/purchases-capacitor` 13.7.4 (npm, 2026-10-13) pide `@capacitor/core >= 8.0.0` y trae
  `purchases-hybrid-common` 19.12.0 → SDK de Android `purchases` 10.27.0 (POM en Maven Central). La versión
  mínima con Test Store no está en la página publicada; un cambio de docs sin fusionar dice Android 9.9.0 e
  iOS 5.43.0 [Likely: 10.27.0 la cumple].
- **Qué falta para decidir.** Con la Test Store se puede integrar y probar el flujo nativo en el APK de
  depuración sin pagar nada; el cobro real sigue necesitando H.2 (StoreKit) y H.3 (Play Billing). Propuesta
  en la fila 17.14; no se escribe la pantalla hasta que el dueño lo decida (Paddle y `/checkout` web no se
  tocan, H.29).

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
**Terceros:** RevenueCat / Paddle (pagos), Groq (IA — texto de preguntas y la pregunta del alumno al tutor, sin nombre ni email), Sentry (opcional, crash logs).  
**Borrado:** `DELETE /api/v1/auth/me/account` + pantalla `/delete-account`.  
**Export:** `GET /api/v1/export/data` (GDPR Art. 20).

---

## 7. Bloqueadores actuales

| Bloqueador | Afecta | Tarea |
|---|---|---|
| H.2 (Apple Developer Program) | iOS submission | 17.14, 19.2 |
| H.3 (Google Play Console) | Android submission | 19.3 |
| 17.14 (RevenueCat IAP) | App Store 3.1.1 | Requiere H.2 |
| 19.2 (Sign in with Apple) | App Store 4.8 (si hay OAuth) | Requiere H.2 |

### Límites de los servicios, comprobados el 2026-10-20

Lo que no lleva URL y fecha aquí es memoria y no vale (regla de la tarea D).

| Servicio | Qué | Fuente (consultada el 2026-10-20) |
|---|---|---|
| Apple Developer Program | 99 USD al año (Enterprise, 299) | <https://developer.apple.com/support/enrollment/> |
| Apple, cuenta gratuita («Personal Team») | Xcode instala en el propio iPhone: hasta 3 dispositivos y 10 App IDs, que caducan a los 7 días; hasta 3 apps por dispositivo; el perfil caduca a los 7 días y hay que recompilar e instalar otra vez | <https://developer.apple.com/support/compare-memberships/> |
| Google Play Console | 25 USD una vez | <https://support.google.com/googleplay/android-developer/answer/6112435> |
| Google Play, cuenta personal creada después del 13-11-2023 | Antes de Producción: prueba cerrada con **al menos 12 testers** apuntados **14 días seguidos**; Producción y Prerregistro desactivados hasta entonces | <https://support.google.com/googleplay/android-developer/answer/14151465> |
| Codemagic, cuenta personal gratuita | 500 min/mes **solo en macOS M2** (`mac_mini_m2`); Linux y Windows **sin** minutos gratis (0,045 $/min); historial y artefactos 30 días; sin colaboradores | <https://docs.codemagic.io/billing/pricing/> (actualizada el 2026-09-21) |
| Codemagic, máquina macOS | Trae SDK de Android (`platforms;android-36.1`, `build-tools;36.1.0`), Gradle 8.14.1 y JDK 17 por defecto: el APK también sale de los minutos gratis | <https://docs.codemagic.io/specs-macos/xcode-26-4> (actualizada el 2026-09-06) |
| Codemagic, flujos sin `triggering` | Solo arrancan a mano | <https://docs.codemagic.io/yaml-running-builds/starting-builds-automatically/> (actualizada el 2026-09-08) |
| Capacitor 8, iconos y splash | La herramienta oficial es `@capacitor/assets` (`npx capacitor-assets generate`, fuente ≥ 1024 px). Aquí se usa `frontend/scripts/generate-icons.mjs`, que dibuja cada tamaño desde los SVG de `design/brand/` con la zona segura medida; sus salidas de Android coinciden byte a byte con las de git (comprobado el 2026-10-20) | <https://capacitorjs.com/docs/guides/splash-screens-and-icons> |
| Capacitor, `server.hostname` | Por defecto `localhost`; se recomienda mantenerlo por las API que exigen contexto seguro (geolocalización, cámara), que la app no usa. Con `androidScheme: https`, `https://app.whetzy.com` también es contexto seguro | `cli/src/declarations.ts` de ionic-team/capacitor (rama `main`) |
| RevenueCat | Ver §4 | §4 |

---

## 8. Checklist pre-envío

### Ambas tiendas

- [ ] IAP configurado en RevenueCat (17.14)
- [ ] Screenshots de 5 pantallas generados y committeados en `docs/store/screenshots/`
- [ ] Cuenta de revisión creada (`reviewer@whetzy.com`)
- [ ] Privacy policy URL configurada en la consola
- [ ] Borrado de cuenta URL en la ficha (Play Store lo exige)

### iOS adicional

- [ ] Cuenta del Apple Developer Program (H.2, 99 USD al año)
- [ ] Sign in with Apple live (19.2) si existe otro OAuth
- [ ] `PrivacyInfo.xcprivacy` actualizado (ya existe en `docs/store/ios/`)
- [ ] Build firmado subido a App Store Connect

### Android adicional

- [ ] Data Safety form rellenado (ver §6 de `play-store-data-safety.md`)
- [x] `targetSdkVersion ≥ 35` (36, comprobado en el APK de depuración el 2026-10-20 con `aapt2 dump badging`)
- [x] Permisos solo de red, vibración y avisos (APK del 2026-10-20; guarda `frontend/src/test/android.permisos.test.ts`)
- [ ] Cuenta de Play Console (H.3, 25 USD una vez)
- [ ] Clave de firma de *release* (keystore) creada y guardada fuera del repo; grupo `android_credentials` en Codemagic
- [ ] **Prueba cerrada: 12 testers durante 14 días seguidos** antes de poder pedir Producción (cuenta personal; §7)
- [x] `BACKEND_CORS_ORIGINS` de Railway con `https://app.whetzy.com` y `capacitor://app.whetzy.com`: hecho y comprobado el 2026-10-21 (RUNBOOK, «App Android de depuración»)
- [ ] Avisos nativos (FCM): hoy la app solo tiene Web Push, que el WebView de Android no ofrece
- [ ] AAB firmado subido a Play Console
