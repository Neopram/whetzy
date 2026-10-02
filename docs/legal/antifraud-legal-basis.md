# Anti-fraud Legal Basis — ePrivacy / GDPR (29.5 → 21.3)

> BORRADOR — pendiente de revisión legal (H.20)

## Base legal: interés legítimo (art. 6.1.f RGPD)

El sistema anti-fraude de Whetzy procesa los siguientes datos con base en el
interés legítimo del responsable para prevenir el abuso del programa de
referidos y la economía de créditos:

### Datos procesados

| Dato | Tratamiento | Retención |
|------|-------------|-----------|
| Hash SHA-256 de huella de dispositivo (UA + timezone + screen + lang) | Comparación contra activaciones previas | 30 días desde la creación |
| Hash SHA-256 de dirección IP | Comparación contra activaciones previas | 30 días desde la creación |
| Email normalizado | Detección de auto-referido | Mientras la cuenta exista |
| Dominio del email | Comparación contra lista pública de dominios desechables | Sin almacenamiento (evaluación en tiempo real) |
| Contador de activaciones por referidor/semana | Detección de velocidad anómala | 7 días (ventana deslizante) |

### Medidas de minimización

1. **Solo hashes**: nunca se almacena la huella o IP en claro; el hash HMAC con
   sal rotativa impide la reversión.
2. **Sin terceros**: no se usa ningún servicio de fingerprinting externo
   (ADR-11).
3. **Retención mínima**: los registros de dispositivo caducan a los 30 días.
4. **Proporcionalidad**: el procesamiento se limita al momento de activación de
   un referido; no hay seguimiento continuo.

### Ponderación de intereses

- **Interés del responsable**: prevenir el fraude en el programa de referidos
  (granjas de cuentas, auto-referidos, dominios desechables) que devaluaría la
  economía de créditos para todos los usuarios.
- **Impacto en el interesado**: mínimo — solo se procesan hashes no reversibles
  en el momento de la activación; no hay perfilado ni seguimiento.
- **Expectativa razonable**: un usuario que participa en un programa de
  referidos espera razonablemente que se verifique la legitimidad de las
  activaciones.

### Derechos del interesado

- **Acceso** (art. 15): el usuario puede solicitar los hashes asociados a su
  cuenta (no son datos personales una vez hasheados, pero se facilitan por
  transparencia).
- **Supresión** (art. 17): la eliminación de la cuenta borra todos los
  registros de `device_fingerprints` y `fraud_review_queue`.
- **Oposición** (art. 21): el usuario puede oponerse; la consecuencia es la
  desactivación del programa de referidos para su cuenta.

---

## Legal Basis: Legitimate Interest (Art. 6(1)(f) GDPR)

Whetzy's anti-fraud system processes the following data under the controller's
legitimate interest in preventing abuse of the referral programme and credit
economy:

### Data Processed

| Data | Processing | Retention |
|------|-----------|-----------|
| SHA-256 hash of device fingerprint (UA + timezone + screen + lang) | Comparison against prior activations | 30 days from creation |
| SHA-256 hash of IP address | Comparison against prior activations | 30 days from creation |
| Normalised email | Self-referral detection | While account exists |
| Email domain | Comparison against public disposable-domain list | No storage (real-time evaluation) |
| Activations per referrer per week | Anomalous velocity detection | 7 days (sliding window) |

### Minimisation Measures

1. **Hashes only**: the raw fingerprint and IP are never stored; HMAC hashing
   with a rotating salt prevents reversal.
2. **No third parties**: no external fingerprinting service is used (ADR-11).
3. **Minimal retention**: device records expire after 30 days.
4. **Proportionality**: processing is limited to the moment of referral
   activation; there is no continuous tracking.

### Balancing Test

- **Controller interest**: preventing referral fraud (account farms,
  self-referrals, disposable domains) that would devalue the credit economy for
  all users.
- **Impact on data subject**: minimal — only non-reversible hashes are processed
  at the moment of activation; no profiling or tracking.
- **Reasonable expectation**: a user participating in a referral programme
  reasonably expects that activations will be verified for legitimacy.

### Data Subject Rights

- **Access** (Art. 15): users may request the hashes linked to their account.
- **Erasure** (Art. 17): account deletion removes all `device_fingerprints` and
  `fraud_review_queue` records.
- **Objection** (Art. 21): users may object; the consequence is deactivation of
  the referral programme for their account.

---

## Para publicar — propuesta de la sesión (2026-10-02; decide el dueño)

**Lo que falta (verificado en el código el 2026-10-02):** la política publicada
(`legal.privacyL1`–`L5`, la fuente según ADR-55) enumera lo que se recoge y no
nombra ni la IP ni el navegador. Pero ya se guardan **en claro** la IP en
`login_attempts`, `user_sessions` y `audit_log`, y el navegador (user agent) en
`user_sessions` y `audit_log`, sin retención por tiempo: solo se borran con la
cuenta. Este borrador dice «nunca se almacena la IP en claro», que vale para
`device_fingerprints` y no para esas tablas. Y el antifraude por dispositivo
(§3.5 de ECONOMIA) no puede encenderse sin declararlo.

**Texto propuesto** (una línea nueva en «1. Información que recopilamos» y otra en
«2. Cómo usamos tus datos»; la base legal ya cubre «interés legítimo… seguridad»):

- ES, recopilamos: «Dirección IP y navegador de cada inicio de sesión, y una huella
  cifrada del dispositivo y de la IP al activar un referido (nunca en claro)».
- ES, usos: «Proteger tu cuenta (bloqueo por intentos, sesiones abiertas) y evitar
  el abuso del programa de referidos».
- EN, we collect: «IP address and browser of each sign-in, and a hashed fingerprint
  of the device and IP when a referral is activated (never in plain text)».
- EN, uses: «Protecting your account (lockout after failed attempts, open sessions)
  and preventing abuse of the referral programme».

**Retención a decidir:** proponemos 90 días para `login_attempts` y `audit_log`, y
la vida de la sesión para `user_sessions`; hoy no hay ninguna. Hasta que el dueño
apruebe el texto, el antifraude por dispositivo/IP sigue apagado (el frontend no
manda `X-Device-Fingerprint`).
