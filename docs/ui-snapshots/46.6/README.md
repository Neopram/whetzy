# Capturas: encuesta de la primera sesión (fila 46.6)

Evidencia de la primera parte de 46.6 (medición). Tras la primera sesión de cada navegador, el resumen
pregunta «¿Te ha servido esta sesión?» con tres respuestas cerradas (Mucho, Algo, Poco) y «Ahora no».

**Cómo se capturaron.** `e2e/encuesta-primera-sesion.spec.ts`, Playwright (Chromium) contra `vite` y el
backend local con datos reales, el 2026-10-21, en ES a 390 y a 1280 px:

- `encuesta-es-*`: el resumen con la encuesta;
- `gracias-es-*`: tras pulsar «Algo».

**Lo que comprueba la misma prueba:**
- axe (WCAG 2.2 AA): 0 violaciones en el resumen con la encuesta, en los dos anchos;
- la respuesta sale en el lote de `/analytics/client-events` como
  `{"type": "first_session_survey", "answer": "somewhat"}`, sin texto libre;
- en la segunda sesión ya no se pregunta.

**Reglas (ADR-68):** el servidor la guarda sin `user_id` ni IP, con esquema cerrado (cualquier
otra respuesta o campo es un 422). Si el navegador pide no ser seguido (GPC o DNT), o no hay
sesión, la encuesta no se enseña, porque su respuesta se tiraría. Lo cubre
`src/test/medicion.46-6.test.tsx`; la versión en inglés solo está en ese test, sin captura.
