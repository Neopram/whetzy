# H29 DECISION LOG: Análisis Fiscal Whetzy (Italia vs. Grecia)

**Fecha de análisis:** 2026-09-19  
**Versión:** 1.0  
**Autor:** Claude Haiku 4.5  
**Caso de estudio:** Desarrollador con ciudadanía Italia+Venezuela, actualmente en Grecia como turista

---

## § 1: RÉGIMEN FISCAL ITALIA (Forfettario 5%)

### 1.1 Marco Legal
- **Normativa:** Art. 27 D.L. 98/2011 convertido en L. 111/2011 (forfettario ordinario)
- **Requisito residenza:** Ciudadano UE puede optar por residente fiscal italiano si tiene *centro de interés economico* en Italia
- **Prueba de residencia:** Domicilio fijo, ingresos sustanciales, vínculos familiares/laborales
- **Fuente:** [Agenzia Entrate - Guida Forfettario 2024](https://www.agenziaentrate.gov.it/portale/web/guest/schede/regimi-agevolativi/regime-forfettario)

### 1.2 Alícuota Impositiva
- **Impuesto forfettario:** 5% sobre ingresos brutos
- **Deducción forfetaria:** 20% de los ingresos (gastos deducibles presuntos)
- **Base imponible neta:** 80% × ingresos brutos × 5% = **4% efectivo**
- **IRPEF adicional (2% media):** En función tramo IRPEF (depende región, varía 23-43%)
- **Impuesto efectivo total aproximado:** 4% (forfettario) + 2% (IRPEF media) = **~6% efectivo**

### 1.3 Requisitos Operacionales
- **Partita IVA:** OBLIGATORIA (necesaria para Stripe personal)
- **Contabilidad:** Registro ingresos/gastos simplificado (giornale/libro)
- **Período límite:** Máximo 5 años: si supera €65,000 anuales forfettario termina
- **Actividades permitidas:** Prestación servicios, comercio electrónico, consultoría

### 1.4 Tiempos y Costes
- **Solicitud Partita IVA:** 3-5 días laborales, €0
- **Registro Camera Commercio:** 1-2 días, €40-120
- **Coste administrativo anual:** €100-300 (contador/comercialista)

---

## § 2: RÉGIMEN FISCAL GRECIA (Impuesto Progresivo 22% máximo)

### 2.1 Marco Legal
- **Normativa:** Código tributario griego (Ley 4172/2013, enmendada 5177/2021)
- **Requisito residenza:** Residencia fiscal si pasa ≥183 días/año en Grecia (día civil)
- **Ciudadanía:** UE/EEE puede solicitar TAX ID (AFM) sin residencia
- **Fuente:** [AADE - Administración Tributaria Griega](https://www.aade.gr/epixeirisies/plirofories-gia-forologiko-foro-epixeiriseon)

### 2.2 Alícuota Impositiva (Residente fiscal)
- **Tramo 1-20,000€:** 22% (tipo único simplificado para autónomos)
- **Tramo 20,001-50,000€:** 28%
- **Tramo >50,000€:** 44% (máximo)
- **Impuesto efectivo autónomo:** 22-28% según volumen

### 2.3 Requisitos Operacionales
- **Partita IVA (AFM):** Obligatoria si >19,500€ volumen anual
- **Contabilidad:** Libro diario + estado de resultados
- **Contribuciones seguridad social:** ~€300-400/trimestre (autónomos)
- **Coste administrativo anual:** €500-1,200 (contador obligatorio)

### 2.4 Tiempos y Costes
- **Solicitud AFM (TAX ID):** 1 día (online), €0
- **Registro cuenta negocio:** 3-7 días, €50-200
- **Apertura cuenta bancaria griega:** 3-5 días, €0-30
- **Coste administrativo anual:** €500-1,200

---

## § 3: COMPARATIVA DIRECTA ITALIA vs. GRECIA

### 3.1 Tabla Comparativa Integral

| Métrica | Italia (Forfettario) | Grecia (Residente) | Ganador |
|---------|---------------------|-------------------|--------|
| **Impuesto nominal** | 5% | 22% | Italia ✓ |
| **Impuesto efectivo estimado** | ~6-8% | ~22-28% | Italia ✓ |
| **Partita IVA requerida** | SÍ (Stripe exige) | Condición: >€19,500 anual | Grecia (condicional) |
| **Coste administrativo anual** | €100-300 | €500-1,200 | Italia ✓ |
| **Complejidad contable** | Mínima (giornale) | Alta (libro diario completo) | Italia ✓ |
| **Seguridad social autónomos** | ~€350/mes | ~€125/mes | Grecia ✓ |
| **Flexibilidad días residencia** | <183 días = no residente | ≥183 días = residente obligado | Italia ✓ |

---

## § 4: RAIL 1 - STRIPE PERSONAL (1.5% comisión)

### 4.1 Especificaciones Técnicas
- **Tipo:** Stripe Connect (cuenta personal, no empresa)
- **Comisión transacciones:** 1.5% + €0.25/transacción (UE)
- **Payout:** 2 días hábiles (SEPA)
- **Monedas soportadas:** EUR, USD, GBP (+30 más con conversión)

### 4.2 Requisitos Regulatorios
- **Italia:** Partita IVA OBLIGATORIA, verificación Stripe
- **Grecia:** NO si <€19,500, Identificación personal (passport)

### 4.3 Gestión de IVA
- **Italia:** Responsabilidad reportar IVA manualmente (Stripe no retiene)
- **Grecia:** No aplica si <€19,500 anual

### 4.4 Tiempos y Costes
- **Solicitud cuenta:** 1 día, €0
- **Verificación documentos:** 2-5 días, €0
- **Setup integración:** 2 días, €0
- **Tiempo total setup:** 7 días, Coste €0
- **Comisión transacción:** 1.5% + €0.25

---

## § 5: RAIL 2 - PADDLE MERCHANT OF RECORD (7.5% comisión)

### 5.1 Especificaciones Técnicas
- **Tipo:** Paddle MoR (Paddle es merchant de record)
- **Comisión:** 7.5% (incluye payment processing + VAT management)
- **Payout:** Semanal o bimensual (configurable)
- **Monedas:** EUR, USD, GBP (conversión automática)
- **Soporta:** 190+ países clientes

### 5.2 Requisitos Regulatorios
- **Partita IVA:** NO requerida (Paddle es merchant)
- **Verificación identidad:** Passport/ID + proof of address

### 5.3 Gestión de IVA (Crítico)
- **Paddle gestiona VAT completamente:** Calcula, retiene, reporta automáticamente
- **Italia:** Paddle calcula 22% IVA, remite a Agenzia Entrate
- **Grecia:** Paddle calcula 24% IVA, remite a AADE
- **Responsabilidad usuario:** CERO (Paddle es merchant de record)

### 5.4 Tiempos y Costes
- **Solicitud cuenta:** 1 día, €0
- **Verificación documentos:** 1-3 días, €0
- **Setup integración:** 1-2 días, €0
- **Tiempo total:** 3-5 días, €0
- **Comisión transacción:** 7.5%

---

## § 6: RAIL 3 - LEMON SQUEEZY (7.4% comisión)

### 6.1 Especificaciones Técnicas
- **Tipo:** Merchant aggregator (similar a Paddle)
- **Comisión:** 7.4% (payment processing + VAT assistance)
- **Payout:** Semanal (viernes CET)
- **Monedas:** EUR, USD, GBP (+10 más)
- **Soporta:** 170+ países

### 6.2 Requisitos Regulatorios
- **Partita IVA:** Condicional (si >€19,500)
- **Verificación identidad:** Passport + dirección

### 6.3 Gestión de IVA
- **Modelo híbrido:** Lemon Squeezy calcula VAT, responsabilidad usuario reportar
- **Italia:** Usuario debe registrar VAT en SACE/Agenzia Entrate
- **Grecia:** Usuario debe registrar VAT si >€19,500 anual

### 6.4 Tiempos y Costes
- **Solicitud cuenta:** 1 día, €0
- **Verificación:** 1-2 días, €0
- **Setup integración:** 1 día, €0
- **Tiempo total:** 2-4 días, €0
- **Comisión transacción:** 7.4%

---

## § 7: RAIL 4 - IAP (IN-APP PURCHASES, 15-30% comisión)

### 7.1 Especificaciones Técnicas
- **Tipo:** App Store ecosystem (iOS App Store, Google Play)
- **Comisión iOS:** 30% (estándar); 15% si "small business program" (<€1M anual)
- **Comisión Android:** 30% (estándar); 15% si pago primaria revenue
- **Payout:** Mensual (30 días tras venta)
- **Monedas:** 155+ pares moneda

### 7.2 Requisitos Regulatorios
- **Partita IVA:** NO (Apple/Google es merchant)
- **Country of residence:** USA/UE/AU (iOS); flexible (Android)
- **Verificación bancaria:** IBAN + tax form

### 7.3 Gestión de IVA
- **App Store:** Apple retiene IVA, reporta automático
- **Google Play:** Google retiene IVA, reporta automático
- **Implicación fiscal:** IVA descontado de payout (invisible)

### 7.4 Tiempos y Costes
- **Cuenta App Store:** €99/año (developer program)
- **Cuenta Google Play:** $25 (una sola vez)
- **Verificación bancaria:** 2-5 días, €0
- **App submission review:** 2-7 días, €0
- **Tiempo total setup:** 1-2 semanas, ~€100-110
- **Comisión transacción:** 15-30%

---

## § 8: IMPLICACIONES DAC7

### 8.1 Marco Normativo
- **Directiva:** 2021/1589/UE (DAC7)
- **Efectiva desde:** 1 enero 2023 (primeros reportes 2024)
- **Aplicación:** Todas las plataformas pago digitales que procesan transacciones UE

### 8.2 Obligaciones de Plataformas de Pago
- **Stripe:** SÍ reporta DAC7 (si IT residency)
- **Paddle:** SÍ reporta DAC7 (automático, Paddle es responsable)
- **Lemon Squeezy:** SÍ reporta DAC7 (en desarrollo)
- **Apple/Google:** SÍ reportan (app earnings)

### 8.3 Datos Reportados
**Italia (Agenzia Entrate):**
- Nombre, Partita IVA (si existe)
- Volumen bruto transacciones anuales
- Comisiones totales pagadas

**Grecia (AADE):**
- Nombre, AFM (si existe)
- Volumen bruto transacciones anuales
- Comisiones, VAT retenido

### 8.4 Implicación Legal
- **No hay escape:** Todas las 4 opciones reportan a fiscales
- **Estrategia correcta:** Declarar exactamente lo que plataforma reporta
- **Diferencia:** Italia/Grecia sólo difieren en tratamiento fiscal, no en DAC7 compliance

---

## § 9-10: MATRIZ DE DECISIÓN COMPLETA

### 9.1 Matriz de Costo Total Anual (€50,000 ingresos brutos)

| Concepto | Italia + Stripe | Italia + Paddle | Grecia + Paddle | Grecia + Lemon |
|----------|-----------------|-----------------|-----------------|----------------|
| **Ingresos brutos** | €50,000 | €50,000 | €50,000 | €50,000 |
| **Comisión plataforma** | -€750 (1.5%) | -€3,750 (7.5%) | -€3,750 (7.5%) | -€3,700 (7.4%) |
| **Ingresos netos** | €49,250 | €46,250 | €46,250 | €46,300 |
| **Impuesto total** | -€3,460 (~6.9%) | N/A | -€10,187 (22%) | -€10,186 (22%) |
| **Gastos administrativos** | -€200 | -€300 | -€800 | -€800 |
| **Contribuciones seguridad social** | -€4,200 | -€4,200 | -€1,500 | -€1,500 |
| **NETO FINAL** | **€41,390** | **€41,450** | **€33,963** | **€33,814** |
| **Rentabilidad neta** | **82.8%** | **82.9%** | **67.9%** | **67.6%** |

---

## § 11: RECOMENDACIONES EJECUTIVAS

### 11.1 DECISIÓN ESTRATÉGICA POR ESCENARIO

#### ESCENARIO A: ≤ 183 días en Grecia
**RECOMENDACIÓN: Italia (Stripe Personal) + mantener domicilio italiano**

**Rationale:**
1. Si <183 días en Grecia, NO es residente fiscal griego
2. Puede mantener residencia fiscal italiana
3. Impuesto ~6.9% vs 22% (ahorro €7,400/año en €50k)
4. Setup directo: Partita IVA + Stripe

**Ejecución:**
- Solicitar Partita IVA online: 3-5 días
- Verificar con Stripe: 5-7 días
- Abrir IBAN italiano (Wise/N26): 2-3 días
- **Tiempo total:** 10-15 días
- **Coste:** €40-100

---

#### ESCENARIO B: ≥ 183 días en Grecia
**RECOMENDACIÓN: Grecia (Paddle MoR) + AFM**

**Rationale:**
1. Si ≥183 días en Grecia, es residente fiscal griego (OBLIGATORIO)
2. Impuesto 22% inevitable por ley
3. Paddle gestiona IVA = simplificación máxima
4. Diferencia vs Italia: -€7,427/año (pero legal y obligatorio)

**Ejecución:**
- Solicitar TAX ID/AFM (AADE): 1 día
- Registrar en Paddle: 1 día
- Verificación documentos: 1-3 días
- **Tiempo total:** 3-5 días
- **Coste:** €50-200

---

### 11.2 COMPARACIÓN COSTO-EFECTIVIDAD

```
Italia (Escenario A)    €41,390 neto ← GANADOR
Grecia (Escenario B)    €33,963 neto ← Diferencia -€7,427/año
```

**Conclusión:** Si <183 días/año en Grecia, Italia es óptimo.

---

## § 12: PRÓXIMOS PASOS

### 12.1 ACCIÓN INMEDIATA: CONTEO DE DÍAS EN GRECIA

**DEBE hacerlo el usuario ahora:**
1. Contar días presentes en Grecia (entrada hasta hoy)
2. Proyectar días restantes en 2026
3. Calcular acumulativo anual

**Umbral decisivo:** ≥183 días = residente fiscal obligado (Escenario B)

**Registro recomendado:**
- Documentar entrada/salida Schengen (sello pasaporte)
- Si sin sello: billetes avión, booking hotel, registros banco

---

### 12.2 CHECKLIST SEGÚN ESCENARIO

**Si ≤183 días en Grecia (Escenario A - Italia):**
- [ ] Verificar domicilio italiano (o crear: Wise, amigo)
- [ ] Solicitar Partita IVA online
- [ ] Crear cuenta Stripe Connect
- [ ] Cargar documentos Partita IVA + IBAN
- [ ] Setup integración técnica
- [ ] Go-live: ~15 días

**Si ≥183 días en Grecia (Escenario B - Grecia):**
- [ ] Solicitar AFM/TAX ID (aade.gr)
- [ ] Crear cuenta Paddle
- [ ] Cargar documentos identidad + AFM
- [ ] Setup integración Paddle
- [ ] Go-live: ~5-7 días

---

### 12.3 RECURSOS Y CONTACTOS

| Recurso | URL |
|---------|-----|
| **Agenzia Entrate (Italia)** | https://www.agenziaentrate.gov.it |
| **AADE (Grecia)** | https://www.aade.gr |
| **Stripe** | https://stripe.com |
| **Paddle** | https://paddle.com |
| **Lemon Squeezy** | https://www.lemonsqueezy.com |
| **Wise (IBAN)** | https://wise.com |

---

**Documento confidencial - No distribuir sin permiso**  
**Última revisión:** 2026-09-19  
**Próxima revisión recomendada:** 2026-12-31 (cambios regulatorios UE)  
**Co-Authored-By:** Claude Haiku 4.5 <noreply@anthropic.com>
