# Neurium — Spec: Web completa (neurium.app)

> Decisión estratégica: no una landing page estática — la plataforma central de Neurium.
> Un backend, tres superficies. Cloudflare Pages, gratis. Registrar dominio hoy.

---

## 1. Estructura del sitio

```
neurium.app
│
├── /                    → Home + hero + conversión
├── /features            → El motor adaptativo explicado visualmente
│                          (FSRS, BKT, Elo, Pyodide — diferenciadores)
├── /pricing             → Free / Pro $9.99 / Pro+ $19.99
│                          + calculadora de ahorro anual
├── /certifications      → Marketplace de bootcamps (Fase 4+)
├── /creators            → Para creadores: cómo publicar su bootcamp
│                          (Fase 4+)
├── /blog                → SEO — artículos técnicos sobre Python, AI,
│                          preparación para certs (tráfico orgánico)
├── /app                 → La PWA de Neurium (acceso web)
│                          Login → estudia desde el navegador
├── /legal
│   ├── /privacy-policy  → Requerido por tiendas y Stripe
│   ├── /terms-of-service
│   └── /delete-account  → REQUERIDO por Google Play (Guideline)
│                          Formulario para borrar cuenta y datos
└── /support             → FAQ + contacto
```

---

## 2. Arquitectura de tres superficies — un solo backend

```
┌─────────────────────────────────────────────────────┐
│                  Backend FastAPI                    │
│         (Railway / Fly.io — un solo deploy)         │
│              PostgreSQL + Redis                     │
└──────────────────┬──────────────────────────────────┘
                   │  API REST /api/v1/*
        ┌──────────┴──────────────────────────┐
        ▼                    ▼                 ▼
   neurium.app/app        App Store        Google Play
   (PWA / browser)        (iOS nativo)    (Android nativo)
   React + Vite           Capacitor        Capacitor
   Cloudflare Pages       Mismo código     Mismo código
```

**Una sola cuenta. Un solo backend. Progreso sincronizado.**
- XP, rachas, ligas, badges — todo en PostgreSQL
- El usuario puede empezar en la web y continuar en el móvil
- Sin duplicación de datos ni lógica

---

## 3. Modelo de pagos: Stripe web + RevenueCat nativo

### El modelo Netflix/Spotify

Apple y Google **solo pueden exigir IAP para compras iniciadas dentro de la app nativa**.
Las suscripciones iniciadas en la web no están sujetas a esa comisión.

```
USUARIO EN WEB (neurium.app/pricing)
    → Hace clic en "Pro $9.99/mes"
    → Paga con Stripe (tarjeta, PayPal, SEPA)
    → Backend activa suscripción en DB
    → La app nativa lee el estado de suscripción vía /api/v1/me
    → Sin comisión Apple/Google (0%)

USUARIO EN APP NATIVA (iOS)
    → Hace clic en "Ir Pro"
    → RevenueCat → StoreKit → Apple IAP
    → Comisión Apple: 15% (primer año) o 30%
    → RevenueCat sincroniza el estado de suscripción

USUARIO EN APP NATIVA (Android)
    → RevenueCat → Google Play Billing
    → Comisión Google: 15% (primeros $1M) o 30%
```

**La app nativa NO muestra el precio ni el botón de pago para iOS.**
Solo muestra: "Gestiona tu suscripción en neurium.app"

### RevenueCat como capa de abstracción

RevenueCat unifica StoreKit (iOS) + Play Billing (Android) + Stripe (web) en una sola API.
El backend consulta RevenueCat para verificar el estado de suscripción de cualquier usuario,
independientemente de por dónde pagó.

```python
# backend — verificar suscripción (pseudocódigo)
async def get_subscription_status(user_id: str) -> SubscriptionTier:
    # 1. Stripe (web)
    stripe_sub = await stripe_client.get_active_subscription(user.stripe_customer_id)
    if stripe_sub:
        return SubscriptionTier.from_stripe(stripe_sub)
    
    # 2. RevenueCat (iOS + Android)
    rc_info = await revenuecat_client.get_subscriber(user.rc_app_user_id)
    if rc_info.active_entitlements:
        return SubscriptionTier.from_revenuecat(rc_info)
    
    return SubscriptionTier.FREE
```

---

## 4. Página `/delete-account` — requerido por Google

**Google Play exige** que los usuarios puedan borrar su cuenta y datos **desde la web**,
no solo desde la app. Esta página es bloqueante para la aprobación en Play Store.

```
neurium.app/delete-account
├── Formulario: email + confirmación
├── Explica qué datos se borran (cuenta, progreso, respuestas)
├── Botón: "Eliminar mi cuenta y datos"
└── Backend: DELETE /api/v1/users/me/account
    → Borra: users, user_skill_states, study_sessions,
              responses, user_badges, user_missions,
              league_entries, stripe_customer, refresh_tokens
    → Envía email de confirmación
    → Tiempo de retención: 30 días (GDPR) antes del borrado permanente
```

---

## 5. Stack técnico

| Componente | Tecnología | Hosting | Coste |
|---|---|---|---|
| Web marketing | Next.js 15 (App Router) | Cloudflare Pages | Gratis |
| PWA (`/app`) | React + Vite (existente) | Cloudflare Pages | Gratis |
| Backend API | FastAPI (existente) | Railway / Fly.io | ~$5-20/mes |
| Base de datos | PostgreSQL | Railway / Supabase | ~$0-25/mes |
| Cache | Redis | Upstash (serverless) | ~$0-10/mes |
| Pagos web | Stripe | — | 2.9% + $0.30/tx |
| Pagos nativo | RevenueCat | — | Gratis hasta $2.5K MRR |
| Dominio | neurium.app | Cloudflare Registrar | ~$12/año |
| Email | Resend | — | Gratis hasta 3K/mes |

**Coste total infraestructura en MVP:** ~$15-55/mes

---

## 6. SEO y captación orgánica

El blog en `/blog` es el canal de captación orgánica a largo plazo.
Artículos objetivo (alto volumen de búsqueda, baja competencia):

- "Cómo preparar el examen AWS Cloud Practitioner en 30 días"
- "GIL de Python explicado con código ejecutable"
- "FSRS vs Anki: cuál es mejor para aprender programación"
- "Preparar CompTIA Security+ gratis: guía completa"
- "asyncio en Python: el error que comete el 80% de los devs"

Cada artículo → embed de una pregunta de Neurium ejecutable vía Pyodide →
llamada a la acción → registro en neurium.app.

---

## 7. Orden de construcción

**Inmediato (antes del deploy):**
1. Registrar `neurium.app` en Cloudflare Registrar
2. Configurar Cloudflare Pages con deploy desde GitHub

**Fase 0 (junto al deploy del backend):**
3. Página `/` (Home) — hero + pitch del motor + CTA
4. Página `/legal` — privacy, terms (ya existen en `privacy-policy.md`)
5. Página `/delete-account` — formulario + endpoint en backend
6. Ruta `/app` — sirve la PWA existente

**Fase 7 (junto a pagos y stores):**
7. Página `/pricing` — tiers + Stripe checkout
8. Integrar RevenueCat para iOS/Android
9. Páginas `/features` y `/certifications`

**Criterio de aceptación mínimo (para Google Play):**
`/delete-account` funcional + `/privacy-policy` en URL pública.
