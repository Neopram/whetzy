# Whetzy — Guía de release definitiva

> Actualizado: 2026-09-15. Serie 17.9 — DONE.
> Changelog completo: [docs/CHANGELOG.md](CHANGELOG.md)
> iOS listing y PrivacyInfo: [docs/store/ios/](store/ios/)
> Play Store Data Safety: [docs/store/play-store-data-safety.md](store/play-store-data-safety.md)

---

## 1. Web (Cloudflare Pages)

### Pre-requisitos
- Node 20, `npm ci` limpio
- Variables de entorno en Cloudflare: `VITE_API_URL=https://api-production-9751.up.railway.app`

### Build y deploy
```bash
cd frontend
npm run build          # NO usar `vite build` directamente — scripts pre/post-build corren con npm
```

La rama `master` de GitHub está conectada al proyecto de Cloudflare Pages (`whetzy`).
**El deploy es MANUAL** (no hay webhook automático — H.11).

```bash
# Verificar que el build nuevo está activo
curl -s https://whetzy.com/assets/ | head -5   # debe mostrar index-HASH.js del build reciente
```

### Checks antes de publicar
```bash
npm run build 2>&1 | grep -E "error|warning"   # 0 errores
node scripts/check-bundle.mjs                   # bundle < 300 KB gz
node scripts/check-no-third-party.mjs           # 0 terceros en dist/
```

### Verificar que el deploy está activo (tras H.11)
```bash
cd frontend
npm run check:deployed                          # 6/6 checks PASS
# Para probar en staging:
npm run check:deployed https://whetzy.pages.dev
```

`check-deployed.mjs` verifica: HTML del build actual · prerender del hero · sitemap.xml · robots.txt · Pyodide autohospedado · 0 terceros en HTML+CSS servido.

### Cloudflare Headers (ya configurado en `public/_headers`)
```
/*
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: credentialless
  Cross-Origin-Resource-Policy: same-site
```

---

## 2. Backend (Railway)

```bash
# Deploy manual desde CLI — Railway token se configura en la UI
railway up --service backend

# O vía dashboard: railway.app → Deployments → Deploy from GitHub
```

### Antes de cualquier deploy
```bash
cd backend
alembic upgrade head        # migraciones pendientes
python -m app.services.content_loader   # cargar contenido si hay cambios (H.SEED)
```

---

## 3. Android (Google Play)

### Pre-requisitos
- Android Studio (o `./gradlew` en CLI) — Java 17+
- Keystore de firma creado y guardado en lugar seguro (**NUNCA en el repo**)
- Google Play Console cuenta activa (H.3 — $25 one-time)

### Build release AAB
```bash
cd frontend
npm run build
npx cap sync android

cd frontend/android
./gradlew bundleRelease \
  -Pandroid.injected.signing.store.file=/ruta/al/whetzy.keystore \
  -Pandroid.injected.signing.store.password=TU_KEYSTORE_PASS \
  -Pandroid.injected.signing.key.alias=TU_KEY_ALIAS \
  -Pandroid.injected.signing.key.password=TU_KEY_PASS
```

AAB generado en: `frontend/android/app/build/outputs/bundle/release/app-release.aab`

### Subir a Play Store
1. Play Console → Whetzy app → Production → Create release
2. Subir el `.aab`
3. Rellenar release notes (ES + EN)
4. Submit for review

### Codemagic CI (alternativa automatizada — free 500 min/month)
Ver `codemagic.yaml` — workflow `android-release` se dispara al crear un tag `v*`.

### assetlinks.json (deep links)
Ya configurado en `public/.well-known/assetlinks.json` — verifica con:
```bash
curl https://whetzy.com/.well-known/assetlinks.json
# Debe devolver el SHA256 del keystore de firma
```

---

## 4. iOS (App Store)

> **H.14 BLOQUEANTE**: iOS requiere macOS + Xcode. No se puede hacer en Windows.
> Opciones gratuitas:
> - **Mac propio o de un amigo**: `npx cap add ios` + `xcodebuild`
> - **Codemagic Mac mini**: $0.095/min — ~$8.55 por build de 90 min (ver `codemagic.yaml`)
> - **GitHub Actions con runner self-hosted macOS**: gratis con tu propio Mac
> - **Expo EAS Build**: free 30 builds/month (requiere migrar a Expo — no recomendado)

### Una vez en macOS

```bash
cd frontend
npm run build
npx cap sync ios    # sync assets to ios/
npx cap open ios    # abre Xcode
```

### En Xcode
1. Signing & Capabilities → Team: tu Apple Developer account (H.2 — $99/año)
2. Bundle ID: `app.whetzy`
3. Version + Build number
4. Product → Archive → Distribute App → App Store Connect

### Pre-submission checklist
- [ ] `PrivacyInfo.xcprivacy` en el bundle (ya preparado en `docs/store/`)
- [ ] `Info.plist`: NSCameraUsageDescription, NSPhotoLibraryUsageDescription (si aplica)
- [ ] Iconos iOS 1024px (generados en `frontend/ios/App/App/Assets.xcassets/AppIcon.appiconset/`)
- [ ] Screenshots 6.5" (iPhone 15 Pro Max) y 12.9" (iPad Pro) — H.9
- [ ] RevenueCat 7.6 IAP configurado antes de submit (B1 — App Store Review blocker)
- [ ] TestFlight: mínimo 1 semana de beta antes de production

---

## 5. Checklist de release completa (web + stores)

| Item | Web | Android | iOS |
|---|---|---|---|
| `npm run build` sin errores | ✅ | ✅ | ✅ |
| `check-bundle.mjs` PASS | ✅ | n/a | n/a |
| `check-no-third-party.mjs` PASS | ✅ | n/a | n/a |
| `alembic upgrade head` en prod | ✅ | ✅ | ✅ |
| Content loader ejecutado (H.SEED) | ✅ | ✅ | ✅ |
| Playwright e2e PASS | ✅ | n/a | n/a |
| Backend health check | ✅ | ✅ | ✅ |
| Signing keystore disponible | n/a | ✅ | ✅ |
| Store listing completo | n/a | ✅ (H.3) | ✅ (H.2) |
| Screenshots en listing | n/a | ✅ (H.9) | ✅ (H.9) |
| RevenueCat IAP | n/a | ✅ (H.5) | ✅ (H.5) |

---

## 6. Versionado

`package.json` es la única fuente de verdad de la versión. `build.gradle` y el proyecto Xcode se actualizan a mano para que coincidan antes de cada release.

| Archivo | Campo | Valor actual |
|---|---|---|
| `frontend/package.json` | `version` | `1.0.0` |
| `frontend/android/app/build.gradle` | `versionName` | `"1.0.0"` |
| `frontend/android/app/build.gradle` | `versionCode` | `1` (incrementar en cada release) |
| `frontend/ios/.../project.pbxproj` | `MARKETING_VERSION` | `1.0.0` (H.14) |

Formato: `MAJOR.MINOR.PATCH` (semver). `versionCode` de Android es siempre creciente (no puede bajar).

```bash
# Antes de cada release:
# 1. Actualizar version en package.json
# 2. Actualizar versionName+versionCode en build.gradle
# 3. Etiquetar en git
git tag v1.0.0
git push origin v1.0.0
```

### Changelog

Mantener [docs/CHANGELOG.md](CHANGELOG.md) actualizado con cada release. Formato: [Keep a Changelog](https://keepachangelog.com/).

---

## 7. Listings de tiendas

### Google Play

Ver [docs/store/play-store-data-safety.md](store/play-store-data-safety.md) para el formulario Data Safety.

**Screenshots requeridos por Play Store (generados con Playwright):**

```bash
cd frontend
npx playwright test e2e/screenshots.spec.ts --headed
# Genera en docs/store/android/screenshots/:
#   phone_1080x1920_*.png   (teléfono)
#   tablet7_1200x1920_*.png (tablet 7")
#   tablet10_1920x1200_*.png (tablet 10")
#   feature_1024x500.png    (feature graphic)
```

> `e2e/screenshots.spec.ts` aún no existe (pendiente de implementar con `page.setViewportSize`). Alternativa manual: capturar desde Chrome DevTools en modo responsive.

**Listing ES/EN:**

| Campo | ES | EN |
|---|---|---|
| Título (50 chars) | Whetzy — Aprende a programar | Whetzy — Learn to Code |
| Descripción corta (80 chars) | Motor adaptativo · bilingüe · Python, AWS, IA · ejecutable | Adaptive engine · bilingual · Python, AWS, AI · runnable |
| Categoría | Educación | Education |

Descripción larga: usar el texto de [docs/store/ios/listing.md](store/ios/listing.md) §Descripción larga (misma para Android).

### iOS App Store

Ver [docs/store/ios/listing.md](store/ios/listing.md) para el listing completo ES/EN, notas del revisor, IAP y screenshots.

`PrivacyInfo.xcprivacy` preparado en [docs/store/ios/PrivacyInfo.xcprivacy](store/ios/PrivacyInfo.xcprivacy) — copiar a `ios/App/App/PrivacyInfo.xcprivacy` al generar el proyecto iOS.

---

## 8. HUMAN-BLOCKED — Acciones solo del dueño

| Bloqueo | Acción | Desbloquea |
|---|---|---|
| **H.11** | Redesplegar frontend en Cloudflare desde `master` | Web visible a usuarios |
| **H.SEED** | `alembic upgrade head` + content loader en prod | Contenido accesible en prod |
| **H.2** | Registrarse en Apple Developer Program ($99/año) | iOS build y App Store |
| **H.3** | Google Play Console ($25) + crear keystore de firma | Android Play Store |
| **H.14** | Mac propio/Codemagic/cloud builder para compilar iOS | App Store submission |
| **H.5** | Completar H.2+H.3+H.14+RevenueCat → submit a tiendas | App en tiendas |
