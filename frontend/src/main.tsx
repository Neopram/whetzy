import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './i18n'
import { registerServiceWorker } from './sw-register'
import { initTheme } from './theme'
import { useAppStore } from './stores/useAppStore'
import { captureAttribution } from './lib/attribution'

// Solo en desarrollo: permite a scripts/ui-snapshots.mjs abrir cada pantalla
// sin pasar por la navegación (currentScreen no se persiste). Vite elimina
// este bloque del build de producción.
if (import.meta.env.DEV) {
  ;(window as unknown as { __whetzyStore?: typeof useAppStore }).__whetzyStore = useAppStore
}

initTheme()
captureAttribution(window.location.search)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

registerServiceWorker()
