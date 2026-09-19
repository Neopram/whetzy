import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { isOffline } from '../../lib/offline'

export function OfflineIndicator() {
  const { t } = useTranslation()
  const [offline, setOffline] = useState(false)

  useEffect(() => {
    const handleOnline = () => setOffline(false)
    const handleOffline = () => setOffline(true)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    setOffline(isOffline())

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (!offline) return null

  return (
    <div style={{
      position: 'fixed',
      bottom: 16,
      left: 16,
      right: 16,
      padding: '8px 12px',
      backgroundColor: '#ef4444',
      color: 'white',
      borderRadius: 8,
      fontSize: 12,
      fontWeight: 600,
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      maxWidth: 'calc(100% - 32px)',
      animation: 'slideUp 0.3s ease-out'
    }}>
      📵 {t('offline.noConnection', 'Sin conexión - Modo offline')}
    </div>
  )
}
