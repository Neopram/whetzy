> **BORRADOR — pendiente de revisión profesional (H.20).** Este documento no ha sido
> revisado por un abogado. No tiene validez legal hasta que el dueño lo apruebe y lo
> publique en la app.

---

# Política de Privacidad / Privacy Policy — Whetzy

**Última actualización / Last Updated:** September 2026

---

## Español

### 1. Información que recopilamos

**Información de cuenta**
- Dirección de correo electrónico, nombre de usuario y avatar de perfil
- Credenciales de autenticación (almacenadas con hash bcrypt; nunca en texto plano)

**Datos de aprendizaje**
- Respuestas a cuestionarios, puntuaciones y marcas de tiempo
- Niveles de dominio de habilidades (p_known BKT) y progreso
- Parámetros de programación de repasos (FSRS, Elo)
- Historial de racha y puntos de experiencia (XP)

**Información del dispositivo**
- Tipo de dispositivo, versión del sistema operativo y versión de la app
- Preferencias de idioma y zona horaria
- Tokens de notificaciones push (si están activadas)

**Analítica de uso**
- Duración y frecuencia de sesiones
- Patrones de interacción con las funciones (anonimizados)
- Informes de errores y métricas de rendimiento

### 2. Cómo usamos tu información

- **Aprendizaje adaptativo:** Tus respuestas y precisión alimentan los algoritmos FSRS,
  Elo y BKT en nuestros servidores para personalizar la dificultad de las preguntas,
  la programación de repasos y las recomendaciones de ruta de aprendizaje.
- **Gamificación:** El seguimiento de la racha, XP, ligas y logros se calcula a partir
  de tu actividad de aprendizaje.
- **Mejora del servicio:** Los datos de uso anonimizados y agregados nos ayudan a mejorar
  la calidad de las preguntas y los resultados de aprendizaje.
- **Comunicaciones:** Notificaciones de correo sobre seguridad de la cuenta, recordatorios
  de racha (si los aceptas) y actualizaciones del producto.

### 3. Bases legales del tratamiento (RGPD)

Si te encuentras en el Espacio Económico Europeo (EEE) o el Reino Unido, tratamos tus
datos con las siguientes bases legales:

| Finalidad | Base legal |
|---|---|
| Proporcionar el servicio de aprendizaje adaptativo | Ejecución del contrato (Art. 6.1.b RGPD) |
| Gamificación (racha, XP, ligas, logros) | Ejecución del contrato |
| Procesamiento de pagos vía Stripe | Ejecución del contrato |
| Seguridad de la cuenta y prevención de fraude | Interés legítimo (Art. 6.1.f) |
| Analítica de uso anonimizada y agregada | Interés legítimo |
| Correos transaccionales (reset, verificación) | Ejecución del contrato |
| Correos de marketing (reactivación) | Consentimiento (Art. 6.1.a) |

### 4. IA y aprendizaje automático

Nuestro motor adaptativo usa modelos de aprendizaje automático (FSRS, BKT, DKT) ejecutados
en nuestros servidores para personalizar tu experiencia. Estos modelos:
- Se ejecutan en los servidores de Whetzy, no en tu dispositivo
- Se entrenan con datos anonimizados y agregados
- No toman decisiones automatizadas que afecten a tus derechos (Art. 22 RGPD)
- Pueden reiniciarse en cualquier momento desde la configuración de tu perfil

El tutor de IA (`/api/v1/tutor/explain`) envía el contexto de la pregunta al servicio de
Groq (proveedor LLM externo) para generar explicaciones. No se envían datos de
identificación personal (nombre, correo, historial de usuario) a Groq.

### 5. Compartir datos

**No** vendemos tus datos personales. Solo compartimos datos:
- Con proveedores de infraestructura bajo acuerdos estrictos de procesamiento de datos:
  - **Railway** (alojamiento del backend y base de datos)
  - **Cloudflare** (CDN y alojamiento del frontend)
  - **Stripe** (procesamiento de pagos — solo datos de facturación)
  - **Groq** (inferencia LLM para el tutor de IA — solo contexto de la pregunta)
- Cuando lo exija la ley o un proceso legal válido
- Con tu consentimiento explícito

### 6. Retención y eliminación de datos

- Cuentas activas: datos retenidos mientras la cuenta está activa
- Eliminación de cuenta: todos los datos personales eliminados en un plazo de 30 días
  (período de gracia RGPD para recuperación)
- Los análisis de aprendizaje anonimizados pueden conservarse indefinidamente
- Solicita la eliminación en cualquier momento desde Ajustes > Eliminar cuenta o por correo

### 7. Privacidad de los menores (COPPA)

Whetzy está destinada a usuarios de 13 años en adelante. Exigimos confirmación de edad
durante el registro. **No recopilamos conscientemente datos de menores de 13 años.** Si
eres padre o tutor y descubres que tu hijo menor de 13 años ha creado una cuenta,
contáctanos en support@whetzy.com y eliminaremos los datos de inmediato.

Para usuarios de 13 a 17 años, requerimos el consentimiento de un padre o tutor según la
jurisdicción aplicable (COPPA para EE. UU., Art. 8 RGPD para la UE — la edad de
consentimiento digital varía de 13 a 16 años según el estado miembro).

### 8. Seguridad

- Todos los datos cifrados en tránsito (TLS 1.3) y en reposo
- Contraseñas almacenadas con bcrypt
- Tokens JWT con caducidad (30 min acceso / 30 días renovación)
- Tokens de restablecimiento de contraseña y verificación de correo almacenados solo
  como hash SHA-256

### 9. Tus derechos

#### 9.1 Derechos bajo el RGPD (EEE y Reino Unido)

Si te encuentras en el Espacio Económico Europeo o el Reino Unido, tienes derecho a:
- **Acceso** (Art. 15): obtener una copia de tus datos — `GET /api/v1/export/data`
- **Rectificación** (Art. 16): corregir datos inexactos — desde tu perfil
- **Supresión** (Art. 17): eliminar tus datos — Ajustes > Eliminar cuenta
- **Limitación del tratamiento** (Art. 18): solicitar la restricción por correo
- **Portabilidad** (Art. 20): descargar tus datos en formato JSON
- **Oposición** (Art. 21): oponerte al tratamiento basado en interés legítimo
- **Reclamación** (Art. 77): presentar una reclamación ante la autoridad de control de
  tu país (p. ej. AEPD en España, CNIL en Francia, ICO en Reino Unido)

#### 9.2 Derechos bajo CCPA/CPRA (California, EE. UU.)

Si eres residente de California, tienes derecho a:
- **Saber** (§1798.100): qué información personal recopilamos, usamos y compartimos
- **Eliminar** (§1798.105): solicitar la eliminación de tu información personal
- **Optar por no participar en la venta/compartición** (§1798.120): `POST /api/v1/privacy/ccpa-opt-out`
  — Whetzy no vende datos, pero este mecanismo está disponible para cumplimiento
- **No discriminación** (§1798.125): no recibirás peor servicio ni precios por ejercer
  tus derechos
- **Corrección** (§1798.106): corregir datos personales inexactos

Categorías de información personal recopilada: identificadores, actividad de internet,
información educativa, geolocalización aproximada, información del dispositivo.
Consulta `GET /api/v1/privacy/ccpa-disclosure` para el detalle completo.

#### 9.3 Derechos bajo otras legislaciones de EE. UU.

- **Virginia (VCDPA)**, **Colorado (CPA)**, **Connecticut (CTDPA)**: derechos similares
  a CCPA — acceso, eliminación, portabilidad, opt-out de publicidad dirigida
- **Utah (UCPA)**: acceso, eliminación, opt-out de venta y publicidad dirigida

Whetzy no realiza publicidad dirigida ni perfilado para toma de decisiones automatizadas.

### 10. Correos electrónicos (CAN-SPAM)

Todos los correos de Whetzy incluyen:
- Identificación clara del remitente
- Línea de asunto precisa y no engañosa
- Mecanismo de cancelación de suscripción (cabecera `List-Unsubscribe`)
- Dirección física del remitente *(pendiente de definir — H.20)*

Puedes desactivar los correos de racha desde Ajustes. Los correos transaccionales
(seguridad, verificación, restablecimiento de contraseña) no se pueden desactivar
porque son necesarios para la operación de tu cuenta.

### 11. Transferencias internacionales de datos

Los datos pueden procesarse en servidores ubicados en la Unión Europea y en los
Estados Unidos. Para transferencias fuera del EEE, nos basamos en:
- Cláusulas contractuales tipo de la Comisión Europea (SCCs)
- Acuerdos de procesamiento de datos con cada proveedor
- Evaluaciones de impacto de transferencias cuando sea necesario

### 12. Cookies

Whetzy utiliza únicamente cookies técnicas necesarias para el funcionamiento del
servicio (token de sesión JWT). **No usamos cookies de seguimiento, publicidad ni
analítica.** Por tanto, no se requiere banner de cookies bajo la Directiva ePrivacy.

### 13. Cambios en esta Política

Te notificaremos los cambios materiales mediante notificación en la app y por correo
electrónico con al menos 30 días de antelación.

### 14. Contacto / Delegado de Protección de Datos

Para consultas sobre privacidad o para ejercer tus derechos:
- Email: **support@whetzy.com**
- Delegado de protección de datos (DPO): *(pendiente de designar — H.20)*

---

## English

### 1. Information We Collect

**Account Information**
- Email address, display name, and profile avatar
- Authentication credentials (bcrypt-hashed, never stored in plain text)

**Learning Data**
- Quiz responses, scores, and timestamps
- Skill mastery levels (BKT p_known) and progress
- Spaced repetition scheduling data (FSRS, Elo parameters)
- Streak and XP history

**Device Information**
- Device type, OS version, and app version
- Language and timezone preferences
- Push notification tokens (if enabled)

**Usage Analytics**
- Session duration and frequency
- Feature interaction patterns (anonymized)
- Crash reports and performance metrics

### 2. How We Use Your Information

- **Adaptive Learning:** Your quiz responses and accuracy power our FSRS, Elo, and BKT
  algorithms on our servers to personalize question difficulty, review scheduling, and
  learning path recommendations.
- **Gamification:** Streak tracking, XP, leagues, and achievements are calculated from
  your learning activity.
- **Service Improvement:** Anonymized, aggregated usage data helps us improve question
  quality and learning outcomes.
- **Communications:** Email notifications about account security, streak reminders (if
  opted in), and product updates.

### 3. Legal Bases for Processing (GDPR)

If you are located in the European Economic Area (EEA) or the United Kingdom, we
process your data under the following legal bases:

| Purpose | Legal Basis |
|---|---|
| Providing the adaptive learning service | Performance of contract (Art. 6.1.b GDPR) |
| Gamification (streak, XP, leagues, achievements) | Performance of contract |
| Payment processing via Stripe | Performance of contract |
| Account security and fraud prevention | Legitimate interest (Art. 6.1.f) |
| Anonymized, aggregated usage analytics | Legitimate interest |
| Transactional emails (reset, verification) | Performance of contract |
| Marketing emails (reactivation) | Consent (Art. 6.1.a) |

### 4. AI & Machine Learning

Our adaptive engine uses machine learning models (FSRS, BKT, DKT) running on our servers
to personalize your learning experience. These models:
- Run on Whetzy's servers, not locally on your device
- Are trained on anonymized, aggregated data only
- Do not make automated decisions that affect your rights (GDPR Art. 22)
- Can be reset at any time from your profile settings

The AI Tutor (`/api/v1/tutor/explain`) sends question context to Groq (external LLM
provider) to generate explanations. No personally identifying data (name, email, user
history) is sent to Groq.

### 5. Data Sharing

We do **not** sell your personal data. We share data only:
- With infrastructure providers under strict data processing agreements:
  - **Railway** (backend hosting and database)
  - **Cloudflare** (CDN and frontend hosting)
  - **Stripe** (payment processing — billing data only)
  - **Groq** (LLM inference for AI Tutor — question context only)
- When required by law or valid legal process
- With your explicit consent

### 6. Data Retention & Deletion

- Active accounts: data retained while account is active
- Account deletion: all personal data deleted within 30 days (GDPR grace period for
  recovery)
- Anonymized learning analytics may be retained indefinitely
- Request deletion at any time via Settings > Delete Account or by email

### 7. Children's Privacy (COPPA)

Whetzy is intended for users aged 13 and older. We require age confirmation during
registration. **We do not knowingly collect data from children under 13.** If you are a
parent or guardian and discover that your child under 13 has created an account, contact
us at support@whetzy.com and we will delete the data promptly.

For users aged 13–17, we require parental or guardian consent as applicable under the
relevant jurisdiction (COPPA for the US, GDPR Art. 8 for the EU — the digital age of
consent varies from 13 to 16 depending on the member state).

### 8. Security

- All data encrypted in transit (TLS 1.3) and at rest
- Passwords stored with bcrypt
- JWT tokens with expiry (30-min access / 30-day refresh)
- Password reset and email verification tokens stored as SHA-256 hash only

### 9. Your Rights

#### 9.1 Rights Under GDPR (EEA and UK)

If you are located in the European Economic Area or the United Kingdom, you have the
right to:
- **Access** (Art. 15): obtain a copy of your data — `GET /api/v1/export/data`
- **Rectification** (Art. 16): correct inaccurate data — from your profile
- **Erasure** (Art. 17): delete your data — Settings > Delete Account
- **Restriction of Processing** (Art. 18): request restriction by email
- **Data Portability** (Art. 20): download your data in JSON format
- **Object** (Art. 21): object to processing based on legitimate interest
- **Complaint** (Art. 77): lodge a complaint with your local supervisory authority
  (e.g. CNIL in France, ICO in the UK, BfDI in Germany)

#### 9.2 Rights Under CCPA/CPRA (California, USA)

If you are a California resident, you have the right to:
- **Know** (§1798.100): what personal information we collect, use, and share
- **Delete** (§1798.105): request deletion of your personal information
- **Opt Out of Sale/Sharing** (§1798.120): `POST /api/v1/privacy/ccpa-opt-out`
  — Whetzy does not sell data, but this mechanism is provided for compliance
- **Non-Discrimination** (§1798.125): you will not receive inferior service or pricing
  for exercising your rights
- **Correction** (§1798.106): correct inaccurate personal information

Categories of personal information collected: identifiers, internet/network activity,
education information, approximate geolocation, device information. See
`GET /api/v1/privacy/ccpa-disclosure` for full details.

#### 9.3 Rights Under Other US State Privacy Laws

- **Virginia (VCDPA)**, **Colorado (CPA)**, **Connecticut (CTDPA)**: similar rights to
  CCPA — access, deletion, portability, opt-out of targeted advertising
- **Utah (UCPA)**: access, deletion, opt-out of sale and targeted advertising

Whetzy does not engage in targeted advertising or profiling for automated decision-making.

### 10. Email Communications (CAN-SPAM)

All Whetzy emails include:
- Clear identification of the sender
- Accurate, non-deceptive subject lines
- An unsubscribe mechanism (`List-Unsubscribe` header)
- Physical mailing address of the sender *(pending — H.20)*

You can disable streak reminder emails from Settings. Transactional emails (security,
verification, password reset) cannot be disabled as they are necessary for your account
operation.

### 11. International Data Transfers

Data may be processed on servers located in the European Union and the United States.
For transfers outside the EEA, we rely on:
- European Commission Standard Contractual Clauses (SCCs)
- Data processing agreements with each provider
- Transfer impact assessments where required

### 12. Cookies

Whetzy uses only strictly necessary technical cookies for service operation (JWT session
token). **We do not use tracking, advertising, or analytics cookies.** Therefore, no
cookie consent banner is required under the ePrivacy Directive.

### 13. Changes to This Policy

We will notify you of material changes via in-app notification and email at least
30 days before they take effect.

### 14. Contact / Data Protection Officer

For privacy inquiries or to exercise your rights:
- Email: **support@whetzy.com**
- Data Protection Officer (DPO): *(pending appointment — H.20)*
