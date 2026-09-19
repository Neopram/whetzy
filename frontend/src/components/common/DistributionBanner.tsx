import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './Button';
import styles from './DistributionBanner.module.css';

/**
 * Distribution Banner Component (Serie 26)
 *
 * Shows promotional banner for YouTube/Dev.to/LinkedIn campaign.
 * Tracks clicks via campaign codes: YT-ES-*, DEV-ES-*, LI-ES-*
 *
 * Props:
 *   dismissible?: boolean - Allow user to close banner (default: true)
 *   locale?: 'es' | 'en' - Language (respects browser lang or user pref)
 *   position?: 'top' | 'bottom' - Banner position (default: 'top')
 *
 * Behavior:
 *   1. Renders ES/EN bilingual CTA
 *   2. Captures ref=YT-ES-SHORT (or other) from URL
 *   3. Sends event to /api/v1/analytics/banner_click
 *   4. Dismissal state saved in localStorage (7-day expiry)
 *
 * Example:
 *   <DistributionBanner locale="es" position="top" />
 */

interface DistributionBannerProps {
  dismissible?: boolean;
  locale?: 'es' | 'en';
  position?: 'top' | 'bottom';
}

export function DistributionBanner({
  dismissible = true,
  locale,
  position = 'top',
}: DistributionBannerProps) {
  const [searchParams] = useSearchParams();
  const [isDismissed, setIsDismissed] = useState(() => {
    if (!dismissible) return false;
    const stored = localStorage.getItem('banner_26_dismissed_at');
    if (!stored) return false;
    const dismissedTime = parseInt(stored, 10);
    return Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000; // 7 days
  });

  // Detect language: prop > browser > fallback to 'es'
  const userLang = locale || (typeof navigator !== 'undefined' ? navigator.language.split('-')[0] : 'es');
  const lang = (userLang === 'en' ? 'en' : 'es') as 'es' | 'en';

  // Capture campaign code from URL
  const campaignCode = searchParams.get('ref') || 'ORGANIC';

  const handleCTAClick = async () => {
    try {
      // Send analytics event
      await fetch('/api/v1/analytics/campaign_click', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_code: campaignCode,
          event_type: 'banner_click_26',
          source: 'distribution_banner',
          timestamp: new Date().toISOString(),
        }),
      }).catch(() => {}); // Silent fail (don't block UX)
    } catch (e) {
      console.warn('[DistributionBanner] Analytics error:', e);
    }

    // Redirect preserving referral code
    const redirectUrl = campaignCode !== 'ORGANIC' ? /?ref= : '/';
    window.location.href = redirectUrl;
  };

  const handleDismiss = () => {
    localStorage.setItem('banner_26_dismissed_at', Date.now().toString());
    setIsDismissed(true);
  };

  const content = {
    es: {
      title: 'Únete a la comunidad ES',
      description: 'Aprende Python adaptativo con motor de IA. Gratuito, certificado real.',
      cta: 'Empieza gratis',
      close: 'Cerrar',
    },
    en: {
      title: 'Join our community',
      description: 'Learn adaptive Python with AI engine. Free, real certificate.',
      cta: 'Start free',
      close: 'Close',
    },
  };

  const text = content[lang];

  if (isDismissed) return null;

  return (
    <AnimatePresence>
      <motion.div
        className={\\ \\}
        initial={{ opacity: 0, y: position === 'top' ? -20 : 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: position === 'top' ? -20 : 20 }}
        transition={{ duration: 0.3 }}
      >
        <div className={styles.content}>
          <div className={styles.text}>
            <h3 className={styles.title}>{text.title}</h3>
            <p className={styles.description}>{text.description}</p>
          </div>

          <div className={styles.actions}>
            <Button
              variant="primary"
              size="sm"
              onClick={handleCTAClick}
              aria-label={text.cta}
            >
              {text.cta}
            </Button>

            {dismissible && (
              <button
                className={styles.closeBtn}
                onClick={handleDismiss}
                aria-label={text.close}
                type="button"
              >
                <span aria-hidden="true">×</span>
              </button>
            )}
          </div>
        </div>

        {/* Campaign code indicator (dev only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className={styles.debug}>{campaignCode}</div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}

DistributionBanner.displayName = 'DistributionBanner';
