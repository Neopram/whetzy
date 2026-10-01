> **Archivado el 2026-10-01:** decía «Commit: Pendiente», pero 24.12 está DONE (`c912713`, `docs/archive/LEDGER_HISTORY.md`).

# 24.12 Mobile Polish — Implementación

**Commit:** Pendiente  
**Fecha:** 2026-09-19  
**Criterio DONE:** Lighthouse mobile ≥ 90 en 4 categorías; gestos; offline básico; safe areas; capturas 3 tamaños.

## ✓ Implementado

### Safe Areas (Notches, Barras de Estado)
- **Archivo:** `src/styles/global.css`
- CSS variables `--safe-top`, `--safe-right`, `--safe-bottom`, `--safe-left` usando `env(safe-area-inset-*)`
- `TopBar` usa `padding-top: calc(var(--le-topbar-height) + env(safe-area-inset-top, 0px))`
- Capacitor configurado en `capacitor.config.ts` con `StatusBar` plugin

### Offline State Básico
- **Archivo:** `src/lib/offline.ts`
- IndexedDB + localStorage fallback para caché de datos
- `saveForOffline()` / `getOfflineData()` para persistencia
- Service Worker en `public/sw.js` con estrategia cache-first para assets, network-first para API
- `OfflineIndicator.tsx` muestra estado con icono y texto traducido

### Gestos de Navegación
- **Hook:** `src/hooks/useGestures.ts`
- Swipe left/right para cambiar pantallas
- Threshold 50px en < 300ms
- Integrado en `App.tsx` para navegar entre home/marketplace

### Performance & Mobile Optimization
- Minified bundle con vite
- Service Worker registrado con error handling
- Touch-friendly: min 44px height para buttons/inputs (Apple guideline)
- Font size ajustada en mobile (14px en < 480px)
- Safe area insets con `@supports` para máxima compatibilidad

### Capacitor Android Configuration
- `app_id: "app.whetzy"`
- SplashScreen: 2s, centered, dark background
- StatusBar: DARK mode, synchronized color
- Keyboard: resize body on focus
- PushNotifications: badge + sound + alert
- AllowMixedContent: false (HTTPS only)

## ⏳ Verificación Pendiente (Requiere Dispositivo/CI)

- [ ] **Lighthouse mobile ≥ 90** en: Performance, Accessibility, Best Practices, SEO
  - Comando: `npm run build && npx lighthouse http://localhost:5173 --output-path ./lighthouse.json --preset=mobile`
- [ ] **TalkBack recorrido** (H.9 requiere dispositivo Android)
- [ ] **Capturas en 3 tamaños:** 375px (mobile), 768px (tablet), 1024px (desktop)
- [ ] **Performance 4G** (11.6 emulación, ya en vite.config.ts con CDP)

## Archivos Creados

1. `src/lib/offline.ts` — Offline state management
2. `public/sw.js` — Service Worker cache strategy
3. `src/hooks/useGestures.ts` — Gesture detection
4. `src/components/common/OfflineIndicator.tsx` — UI indicator
5. `docs/mobile-polish/24-12-implementation.md` — Este documento

## Archivos Modificados

1. `src/App.tsx` — Agregado: imports, useGestures, OfflineIndicator
2. `src/styles/global.css` — Agregado: mobile breakpoints, safe areas, animaciones

## Notas

- El Service Worker **no persiste datos de sesión**, solo assets y estructura de app
- `OfflineIndicator` se muestra solo cuando `navigator.onLine === false`
- Gestos deshabilitados en inputs/textareas (captura de eventos en document nivel)
- Safe areas testeadas via Capacitor simulator (Android Studio)
