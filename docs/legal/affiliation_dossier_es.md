# Dossier de afiliación — Python Institute y CompTIA

*Septiembre 2026 · Documento interno*

---

## Objetivo

Establecer programas de afiliado con **Python Institute** (certificaciones PCEP,
PCAP, PCPP) y **CompTIA** (Security+, Network+, A+) para generar comisiones
sobre los exámenes que nuestros usuarios compren a través de enlaces de referido.

## 1. Python Institute

### Certificaciones relevantes

| Certificación | Track Whetzy | Precio examen | Nivel |
|---|---|---|---|
| **PCEP** — Python Certified Entry-Level Programmer | track01 (Python Básico) | ~$59 | Entrada |
| **PCAP** — Python Certified Associate in Python Programming | track02 (Python Intermedio) | ~$295 | Asociado |
| **PCPP** — Python Certified Professional in Python Programming | — (futuro) | ~$195 | Profesional |

### Programa de afiliados

- **Plataforma**: Python Institute gestiona su programa de afiliados a través de
  Pearson VUE (proveedor del examen).
- **Comisión estimada**: 10-15% por examen vendido a través del enlace de afiliado.
  [Guessing — verificar directamente con Python Institute antes de publicar cifras.]
- **Requisitos esperados**:
  - Cuenta de empresa o educador registrada.
  - Descripción de la plataforma y cómo se usa para preparar candidatos.
  - Aceptación de los términos del programa de afiliados.
- **Contacto**: partners@pythoninstitute.org (verificar en pythoninstitute.org).

### Pasos para aplicar

1. Visitar el sitio web de Python Institute y buscar la sección de partners/affiliates.
2. Completar el formulario de solicitud con:
   - Datos de la empresa (Whetzy).
   - Descripción del producto y público objetivo.
   - Volumen estimado de candidatos (basado en usuarios activos).
3. Recibir aprobación y enlaces de afiliado.
4. Integrar enlaces en la UI de Whetzy (pantalla de certificación, resultados
   del medidor de preparación).

## 2. CompTIA

### Certificaciones relevantes

| Certificación | Track Whetzy | Precio examen | Nivel |
|---|---|---|---|
| **Security+ SY0-701** | track08 (Ciberseguridad) | ~$404 | Profesional |
| **Network+ N10-009** | — (futuro) | ~$369 | Profesional |
| **A+ 220-1101/1102** | — (futuro) | ~$258×2 | Entrada |

### Programa de afiliados

- **Plataforma**: CompTIA tiene un programa de partners y un marketplace.
- **Comisión estimada**: ~10% por compra de voucher de examen a través del enlace.
  [Guessing — verificar directamente con CompTIA antes de publicar cifras.]
- **Tipos de partnership**:
  - **Authorized Delivery Partner**: requiere instalaciones físicas de examen.
  - **Content Partner / Affiliate**: más adecuado para Whetzy — plataforma de
    preparación que refiere candidatos al examen.
- **Contacto**: partners@comptia.org o a través de comptia.org/partners.

### Pasos para aplicar

1. Visitar comptia.org y buscar la sección de partners.
2. Solicitar el programa de Content Partner o Affiliate.
3. Proporcionar:
   - Datos de la empresa.
   - Descripción de los tracks de preparación.
   - Métricas de usuarios (cuando las tengamos: activos, tasa de finalización).
4. Recibir aprobación y vouchers/enlaces de afiliado.
5. Integrar en la pantalla de certificación de Whetzy.

## 3. Modelo de ingresos

| Escenario (mes 6) | Usuarios que toman examen | Examen medio | Comisión | Ingreso mensual |
|---|---|---|---|---|
| Conservador | 20 | $150 | 10% | $300 |
| Moderado | 50 | $200 | 12% | $1.200 |
| Optimista | 100 | $250 | 15% | $3.750 |

**Nota**: las cifras de comisión son estimaciones. Los porcentajes reales se
negocian al formalizar la afiliación. No publicar en ningún documento externo
hasta tener confirmación por escrito del proveedor.

## 4. Integración técnica

- **UI**: botón "Registrarse para el examen" en la pantalla de certificación
  (`CertificationScreen`) con enlace de afiliado parametrizado.
- **Tracking**: UTM params o ID de afiliado en el enlace para atribución.
- **Medidor de preparación**: "Tu probabilidad estimada de aprobar PCEP es X%.
  ¿Listo para registrarte?" con enlace directo.
- **Disclaimer**: "Whetzy no es un centro de exámenes. El examen se realiza a
  través del proveedor oficial."

## 5. Acciones inmediatas

- [ ] Contactar Python Institute (partners/affiliates).
- [ ] Contactar CompTIA (Content Partner program).
- [ ] Obtener confirmación escrita de tasas de comisión.
- [ ] Integrar enlaces de afiliado en la UI cuando estén disponibles.
- [ ] Configurar tracking de conversiones.
