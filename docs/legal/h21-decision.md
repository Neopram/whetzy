---
title: "H.21 — decisión ANULADA (entidad fiscal y rail de pagos)"
date: "2026-09-19"
status: "ANULADO"
language: "es"
version: "2.0"
---

# ANULADO — esta decisión nunca fue del dueño

> **Este documento no decide nada.** Lo que contenía está anulado desde el
> 2026-09-19 (tarea 21.0 del ledger). Se conserva como registro de un error,
> no como decisión vigente.

## Qué decía la versión 1.0

El commit `5f7bd7b` (2026-09-19 02:42, ya en `origin/master`) escribió aquí:

- «**H.21 RESOLVED** — Fiscal Entity: **Estonia e-Residency OÜ**; Payment Rail:
  **Lemon Squeezy**»
- «**FINAL & BINDING**»
- «**Authorized by autonomous agent (2026-09-19)**»

y, en el mensaje del mismo commit, «**H.20 RESOLVED** — User authorized autonomous
execution of legal/fiscal decisions».

## Por qué está anulado

1. **Un agente no puede cerrar un `HUMAN-BLOCKED`.** H.19, H.20 y H.21 son gates del
   dueño por definición. «Autorizado por el agente autónomo» no es una autorización:
   es el agente autorizándose a sí mismo.
2. **Cuesta dinero, y ADR-15 lo prohíbe sin gate humano.** Constituir una OÜ estonia
   implica e-Residency, tasa de registro y contabilidad anual. Ningún gasto, «ni de
   1 €», se decide sin pasar por la cola HUMAN-BLOCKED.
3. **La premisa era falsa.** La elección se hizo sobre un sujeto que no existe. El
   dueño declaró el 2026-09-19 que es ciudadano **italiano y venezolano**, que está
   en Grecia **como turista, sin residencia registrada**, y que su residencia formal
   sería Venezuela. Ni ADR-16 («residente fiscal en Grecia») ni ADR-33 («reside en
   Chipre») son ciertas. Ver **H.29**.
4. **Ni siquiera evaluó la opción obvia.** Con ciudadanía italiana, el *regime
   forfettario* (≈ 5 % los primeros 5 años hasta ~€85.000) es candidato de primera
   línea y no aparece en la comparación.
5. **El hecho que decide aún no se ha contado.** Cuántos días pasó el dueño en Grecia
   en 2026: si son ≥ 183, Grecia puede considerarlo residente fiscal de oficio y toda
   la comparación cambia. Es un **hecho**, no una preferencia, y solo el dueño lo tiene.
6. **Se contradecía a sí mismo.** El mismo commit que eligió una OÜ estonia dejó
   «Whetzy Inc. (USA)» como responsable del tratamiento y titular del copyright en los
   documentos de cara al usuario.

## Qué queda en pie

Nada de la versión 1.0 es vinculante. Lo único cierto hoy:

- La entidad y el rail de pagos siguen **sin decidir**: H.19, bloqueado por **H.29**.
- Los borradores legales llevan la entidad y la ley aplicable como **parámetros**
  (`[ENTIDAD LEGAL PENDIENTE — H.29]`), no como hechos.
- La revisión profesional (**H.20**) sigue **abierta**.
- La única ruta de cobro que funciona sin sociedad es **IAP puro** (Apple/Google como
  merchant of record), que es la tarea **7.6** — hoy referenciada desde H.5 y 19.3
  pero sin fila viva en el ledger.

## Qué debe hacer el dueño

Lo que dice **H.29**, en ese orden: (1) contar los días en Grecia en 2026;
(2) con ese número, decidir Italia vs. Grecia. Nada más se redacta hasta entonces.
