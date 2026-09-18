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

### 3. IA y aprendizaje automático

Nuestro motor adaptativo usa modelos de aprendizaje automático (FSRS, BKT, DKT) ejecutados
en nuestros servidores para personalizar tu experiencia. Estos modelos:
- Se ejecutan en los servidores de Whetzy, no en tu dispositivo
- Se entrenan con datos anonimizados y agregados
- No toman decisiones automatizadas que afecten a tus derechos
- Pueden reiniciarse en cualquier momento desde la configuración de tu perfil

El tutor de IA (/api/v1/tutor/explain) envía el contexto de la pregunta al servicio de
Groq (proveedor LLM externo) para generar explicaciones. No se envían datos de
identificación personal (nombre, correo, historial de usuario) a Groq.

### 4. Compartir datos

**No** vendemos tus datos personales. Solo compartimos datos:
- Con proveedores de infraestructura bajo acuerdos estrictos de procesamiento de datos:
  - **Railway** (alojamiento del backend y base de datos)
  - **Cloudflare** (CDN y alojamiento del frontend)
  - **Stripe** (procesamiento de pagos — solo datos de facturación)
  - **Groq** (inferencia LLM para el tutor de IA — solo contexto de la pregunta)
- Cuando lo exija la ley o un proceso legal válido
- Con tu consentimiento explícito

### 5. Retención y eliminación de datos

- Cuentas activas: datos retenidos mientras la cuenta está activa
- Eliminación de cuenta: todos los datos personales eliminados en un plazo de 30 días
- Los análisis de aprendizaje anonimizados pueden conservarse indefinidamente
- Solicita la eliminación en cualquier momento desde Ajustes > Eliminar cuenta o por correo

### 6. Privacidad de los menores

Whetzy está destinada a usuarios de 13 años en adelante. No recopilamos conscientemente
datos de menores de 13 años. Si descubrimos dichos datos, los eliminaremos de inmediato.

### 7. Seguridad

- Todos los datos cifrados en tránsito (TLS 1.3) y en reposo
- Contraseñas almacenadas con bcrypt
- Tokens JWT con caducidad (30 min acceso / 30 días renovación)
- Tokens de restablecimiento de contraseña y verificación de correo almacenados solo
  como hash SHA-256

### 8. Tus derechos

Dependiendo de tu jurisdicción, puedes tener derecho a:
- Acceder a tus datos personales
- Corregir datos inexactos
- Eliminar tus datos
- Exportar tus datos en formato portátil (GET /api/v1/export/data)
- Optar por no participar en la analítica

### 9. Transferencias internacionales de datos

Los datos pueden procesarse en servidores ubicados en la Unión Europea y en los
Estados Unidos, de conformidad con las leyes de protección de datos aplicables.

### 10. Cambios en esta Política

Te notificaremos los cambios materiales mediante notificación en la app y por correo
electrónico con al menos 30 días de antelación.

### 11. Contacto

Para consultas sobre privacidad: **support@whetzy.com**

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

### 3. AI & Machine Learning

Our adaptive engine uses machine learning models (FSRS, BKT, DKT) running on our servers
to personalize your learning experience. These models:
- Run on Whetzy's servers, not locally on your device
- Are trained on anonymized, aggregated data only
- Do not make automated decisions that affect your rights
- Can be reset at any time from your profile settings

The AI Tutor (/api/v1/tutor/explain) sends question context to Groq (external LLM
provider) to generate explanations. No personally identifying data (name, email, user
history) is sent to Groq.

### 4. Data Sharing

We do **not** sell your personal data. We share data only:
- With infrastructure providers under strict data processing agreements:
  - **Railway** (backend hosting and database)
  - **Cloudflare** (CDN and frontend hosting)
  - **Stripe** (payment processing — billing data only)
  - **Groq** (LLM inference for AI Tutor — question context only)
- When required by law or valid legal process
- With your explicit consent

### 5. Data Retention & Deletion

- Active accounts: data retained while account is active
- Account deletion: all personal data deleted within 30 days
- Anonymized learning analytics may be retained indefinitely
- Request deletion at any time via Settings > Delete Account or by email

### 6. Children's Privacy

Whetzy is intended for users aged 13 and older. We do not knowingly collect data from
children under 13. If we discover such data, we will delete it promptly.

### 7. Security

- All data encrypted in transit (TLS 1.3) and at rest
- Passwords stored with bcrypt
- JWT tokens with expiry (30-min access / 30-day refresh)
- Password reset and email verification tokens stored as SHA-256 hash only

### 8. Your Rights

Depending on your jurisdiction, you may have the right to:
- Access your personal data
- Correct inaccurate data
- Delete your data
- Export your data in a portable format (GET /api/v1/export/data)
- Opt out of analytics

### 9. International Data Transfers

Data may be processed in servers located in the European Union and the United States,
in compliance with applicable data protection laws.

### 10. Changes to This Policy

We will notify you of material changes via in-app notification and email at least
30 days before they take effect.

### 11. Contact

For privacy inquiries: **support@whetzy.com**
