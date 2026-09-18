---
title: "Política de Cookies"
last_updated: "2026-09-19"
effective_date: "2026-10-01"
language: "es"
status: "DRAFT - Requiere revisión legal"
version: "1.0.0"
---

# Política de Cookies

## Aviso Legal

Este es un documento BORRADOR solo para revisión interna. NO aprobado por asesor legal.

---

## 1. ¿Qué son las Cookies?

Las cookies son pequeños archivos de texto almacenados en su dispositivo que ayudan a personalizar su experiencia. Contienen información sobre su comportamiento de navegación y preferencias.

---

## 2. Tipos de Cookies que Usamos

### 2.1 Cookies Esenciales (Siempre Activas)

Necesarias para funcionalidad básica:

- **Identificador de Sesión** (`whetzy_session`): Mantiene estado de login
- **Token de Autenticación** (`whetzy_auth`): Verifica identidad del usuario
- **Protección CSRF** (`whetzy_csrf`): Previene solicitudes no autorizadas
- **Preferencias** (`whetzy_lang`, `whetzy_theme`): Recuerda idioma y tema

Atributos: HttpOnly, Secure, SameSite=Strict

### 2.2 Cookies de Análisis (Opcional)

Para entender comportamiento del usuario:

- **Google Analytics**: `_ga`, `_gat`, `_gid` (hasta 2 años)
  - Propósito: Rastrear comportamiento, conversiones, fuentes de tráfico
  - Optar: Disponible en banner de consentimiento
  - Privacidad: Datos anonimizados y agregados

### 2.3 Cookies de Terceros

- Procesadores de Pago: Stripe, Paddle (transacciones)
- Proveedores de Análisis: Google Analytics
- Proveedores CDN: CloudFlare (si se usa)

---

## 3. Atributos de Cookies

Nuestras cookies usan mejores prácticas de seguridad:

| Atributo | Descripción |
|----------|-------------|
| **HttpOnly** | No accesible por JavaScript (previene XSS) |
| **Secure** | Transmitidas solo por HTTPS |
| **SameSite** | Previene CSRF; configurado a Strict o Lax |
| **Domain** | `.whetzy.com` (subdomains) |
| **Path** | `/` (aplicación completa) |

---

## 4. Consentimiento de Cookies

### 4.1 Consentimiento Implícito

Al continuar usando Whetzy, usted consiente nuestro uso de cookies. Esenciales siempre activas.

### 4.2 Opt-In Explícito

En algunas jurisdicciones, se proporciona:
- Aceptar Todo: Todas las cookies
- Solo Esencial: Desactiva análisis
- Personalizar: Categorías específicas

### 4.3 Deshabilitar Cookies

**Configuración del Navegador:**
- Chrome: Configuración > Privacidad y seguridad > Cookies
- Firefox: Preferencias > Privacidad > Cookies
- Safari: Preferencias > Privacidad > Datos de Sitios Web
- Edge: Configuración > Privacidad > Cookies

**Nota**: Desactivar puede limitar funcionalidad.

### 4.4 Optar por No Participar en Análisis

- Haga clic en "Gestionar Preferencias" en banner
- Desactive "Analytics Cookies"
- Extensión Google: https://tools.google.com/dlpage/gaoptout

---

## 5. Do Not Track (DNT)

No respondemos actualmente a señales DNT. Puede:
- Deshabilitar cookies
- Optar por no participar en análisis
- Contactarnos para medidas adicionales

---

## 6. Cookies de Terceros

| Servicio | Propósito | Optar |
|----------|-----------|-------|
| Google Analytics | Rastreo de comportamiento | https://tools.google.com/dlpage/gaoptout |
| Stripe | Procesamiento de pagos | https://stripe.com/cookies-policy |
| Paddle | Gestión de facturación | https://paddle.com/privacy |
| CloudFlare | CDN/seguridad | https://cloudflare.com/cookie-policy |

---

## 7. Cambios en Esta Política

- Cambios publicados aquí
- Fecha efectiva actualizada
- Cambios materiales: notificación por correo
- Uso continuo = aceptación

---

## 8. Contacto

**Correo**: legal@whetzy.com
**Soporte**: support@whetzy.com

---

Versión: 1.0.0 (BORRADOR)
