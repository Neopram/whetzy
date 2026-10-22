import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './i18n'
import { registerServiceWorker } from './sw-register'
import { initTheme } from './theme'
import { useAppStore } from './stores/useAppStore'
import { captureAttribution } from './lib/attribution'
import { armFeedbackFx } from './lib/feedbackFx'
import { startFxAnalytics } from './lib/fxAnalytics'
import { installNativeBackButton } from './lib/screenHistory'

// Solo en desarrollo: permite a scripts/ui-snapshots.mjs abrir cada pantalla
// sin pasar por la navegación (currentScreen no se persiste). Vite elimina
// este bloque del build de producción.
if (import.meta.env.DEV) {
  ;(window as unknown as { __whetzyStore?: typeof useAppStore }).__whetzyStore = useAppStore
}

initTheme()
captureAttribution(window.location.search)
// 46.2: el sonido y la vibración esperan al primer gesto (política de autoplay).
armFeedbackFx()
// 46.6a (ADR-68): tasa de salto por nivel, anónima.
startFxAnalytics()
// 42.10: en Android, el botón «atrás» vuelve de pantalla; sin historial cierra la app.
void installNativeBackButton()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

registerServiceWorker()
