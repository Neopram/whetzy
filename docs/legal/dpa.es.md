---
title: "RGPD Apéndice de Procesamiento de Datos (DPA)"
last_updated: "2026-09-19"
effective_date: "2026-10-01"
language: "es"
status: "BORRADOR — pendiente de revisión profesional (H.20)"
version: "1.0.0"
---

# RGPD Apéndice de Procesamiento de Datos (DPA)

## Aviso Legal

**BORRADOR — pendiente de revisión profesional (H.20).**

Este es un documento BORRADOR solo para revisión interna. NO aprobado por asesor legal.

---

## 1. Definiciones

- **Responsable del Tratamiento**: el titular del Servicio [ENTIDAD LEGAL PENDIENTE — H.29] (determina propósitos/medios)
- **Interesado**: Usuario que proporciona datos personales
- **Datos Personales**: Información de persona identificada/identificable
- **Tratamiento**: Cualquier operación sobre datos personales
- **RGPD**: Reglamento UE 2016/679

---

## 2. Responsabilidades del Responsable

### 2.1 Rol de Whetzy

Whetzy actúa como Responsable del Tratamiento para:
- Datos de cuenta de usuario
- Datos de progreso y rendimiento
- Datos de dispositivo y analítica
- Información de pago

### 2.2 Base Legal para Procesamiento

Whetzy procesa bajo:
- Contrato (datos de cuenta y aprendizaje)
- Interés legítimo (analítica, prevención de fraude)
- Obligación legal (cumplimiento fiscal)
- Consentimiento (emails de marketing)

### 2.3 Obligaciones de Protección de Datos

Whetzy se compromete a:
- Procesar solo para propósitos especificados
- Recopilar solo datos necesarios
- Mantener datos precisos y actualizados
- Implementar medidas de seguridad
- Respetar derechos del interesado
- Reportar brechas dentro de 72 horas

---

## 3. Derechos del Interesado

### 3.1 Derecho de Acceso

Solicitud: Enviar a legal@whetzy.com
Respuesta: Dentro de 30 días

### 3.2 Derecho de Rectificación

Solicitud: Actualizar en panel o enviar a legal@whetzy.com
Respuesta: Dentro de 30 días

### 3.3 Derecho al Olvido

Motivos: Datos innecesarios, retiro de consentimiento, tratamiento ilegal

Proceso:
1. Solicitud a legal@whetzy.com
2. Eliminación suave: Inmediata
3. Período de gracia: 30 días
4. Eliminación permanente: Después de 30 días

Excepciones: Obligaciones legales, registros de auditoría (90 días), datos anonimizados

### 3.4 Derecho a Restringir Procesamiento

Solicitar limitaciones en uso de datos. Whetzy marca como restringido.

### 3.5 Derecho a Portabilidad

Solicitar datos personales en formato JSON/CSV
Proceso: Email a legal@whetzy.com; export vía API en 30 días

### 3.6 Derecho de Oposición

Oponerse a marketing, procesamiento, perfilado.
Whetzy cesa dentro de 30 días.

### 3.7 Derecho a Retirar Consentimiento

Retirar marketing: Enlace desuscribirse
Retirar analítica: Preferencias de cookies
Otro: Email a legal@whetzy.com

---

## 4. Subprocesadores

### 4.1 Subprocesadores Aprobados

- Railway: hosting y base de datos PostgreSQL (UE)
- Cloudflare: CDN y Pages
- Groq: inferencia del tutor de IA (modelo qwen/qwen3.8-27b)
- Stripe: pagos (hoy solo en modo test, sin cobros reales; la cuenta live está pendiente — H.4)
- Proveedor de email: SMTP o Resend, según la variable EMAIL_PROVIDER
- Sentry: registro de errores del servidor, activo desde el 26-09-2026 (región UE, de.sentry.io; `send_default_pii=False`; no se usa en el navegador)

### 4.2 Cambios de Subprocesadores

Cambios notificados 30 días antes. Derecho a objetar en 30 días.

---

## 5. Seguridad de Datos

### 5.1 Medidas Técnicas

- Cifrado HTTPS/TLS en tránsito
- Cifrado AES-256 en reposo
- Hashing Bcrypt/Argon2 de contraseñas
- 2FA opcional
- Auditorías de seguridad
- Sistemas de detección de intrusiones

### 5.2 Medidas Organizacionales

- Capacitación en protección de datos
- Controles de acceso basados en roles
- Acuerdos de confidencialidad
- Plan de respuesta a incidentes
- Privacidad por diseño

### 5.3 Respuesta a Brechas

- Investigación inmediata
- Notificar autoridad dentro de 72 horas
- Notificar usuarios si riesgo alto
- Documentar brecha y respuesta
- Comunicar con procesadores

---

## 6. Retención y Eliminación de Datos

### 6.1 Cronograma de Retención

- Perfil de cuenta: Activo + 30 días
- Datos de aprendizaje: Solo activo
- Registros de auditoría: 90 días
- Huellas de dispositivo: 30 días
- Registros de pago: 7 años (obligación fiscal)
- Analítica: 30 días individual, indefinido agregado
- Tickets de soporte: 2 años

### 6.2 Proceso de Eliminación

1. Eliminación suave: Anonimización inmediata
2. Período gracia: 30 días
3. Eliminación permanente: Eliminación total
4. Verificación: Email de confirmación
5. Documentación: Registrado en auditoría

---

## 7. Evaluación de Impacto de Protección de Datos

Whetzy realiza evaluaciones para:
- Tratamiento de alto riesgo
- Introducción de nueva tecnología
- Cambios en recopilación/uso
- Tratamiento a gran escala

Evalúan necesidad, riesgos y mitigaciones.

---

## 8. Transferencias Internacionales de Datos

### 8.1 Mecanismo Legal

Transferencias desde EU/UK bajo:
- Cláusulas Contractuales Estándar (CCS)
- Acuerdos de Procesamiento de Datos
- Decisiones de adecuación (donde aplique)

### 8.2 Cumplimiento Schrems II

Siguiendo decisión de Corte de Justicia UE:
- Salvaguardas suplementarias en lugar
- Medidas técnicas para limitar acceso gubernamental USA
- Monitoreo de cambios legales USA
- Opciones alternativas de almacenamiento

---

## 9. Cambios en DPA

Cambios materiales: Aviso de 30 días por email
Cambios no-materiales: Publicados aquí
Uso continuo = aceptación

---

## 10. Resolución de Disputas

### 10.1 Informal

Contacte legal@whetzy.com; período resolución 30 días.

### 10.2 Formal

Presentar queja ante:
- Autoridad Supervisora UE
- ICO Reino Unido
- Autoridad Nacional de Protección de Datos

---

## 11. Ley Aplicable

- Reglamento RGPD 2016/679
- Ley de Protección de Datos 2018 (UK)
- [LEY APLICABLE PENDIENTE — H.29]

---

## 12. Contacto

- **Legal & Protección de Datos**: legal@whetzy.com
- **Soporte**: support@whetzy.com
- **DPO**: A designar
- **Dirección**: A actualizar

---

Versión: 1.0.0 (BORRADOR)

AVISO DE BORRADOR: No aprobado por asesor legal. Requiere revisión formal antes de procesar datos personales de EU/UK.
