import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'app.whetzy',
  appName: 'Whetzy',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    // La app nativa se sirve desde https://app.whetzy.com (Android) y
    // capacitor://app.whetzy.com (iOS), no desde «localhost»: producción
    // descarta a propósito los orígenes loopback en CORS y en el control de
    // Origin (22.2, config.py `active_cors_origins`), así que con «localhost»
    // el login desde el teléfono daba 400 en el preflight (medido el
    // 2026-10-20). Un subdominio propio no lo puede servir nadie más, y con la
    // API en api.whetzy.com la cookie es del mismo sitio. Contrato con el
    // backend: tests/integration/test_cors_app_nativa.py.
    hostname: 'app.whetzy.com',
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#0A0E1A',
      showSpinner: false,
      androidScaleType: 'CENTER_CROP',
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#0A0E1A',
    },
    Keyboard: {
      resize: 'body',
      resizeOnFullScreen: true,
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },
  },
  ios: {
    contentInset: 'automatic',
    preferredContentMode: 'mobile',
    scheme: 'Whetzy',
  },
  android: {
    allowMixedContent: false,
    backgroundColor: '#0A0E1A',
  },
};

export default config;
