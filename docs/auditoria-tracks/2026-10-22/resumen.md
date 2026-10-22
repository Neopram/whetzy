# Resumen de la auditoría de tracks (2026-10-22)

Generado por `scripts/audit_tracks.py` desde `content/` y `scripts/metas_catalogo.json`.
Sin modelos: cada recomendación de las fichas sale de una regla de ese script.

Plan: 56 tracks · construidos: 35 · cuarentena: 2 · planificados: 19.
Construidos: 12037 preguntas · 730 lecciones · 1058 términos.
Construidos sin ningún ejecutable estricto: 22 de 35.
En la forma ADR-54 de aprendizaje (≥ 32 skills; por skill ≥ 10 preguntas, ≥ 3 con código y 1 lección): 1 de 24 construidos de aprendizaje (los términos no llevan skill_id y no se comprueban por skill).
Preguntas huérfanas (skill que no pertenece a ningún track): 0.
Ficheros sueltos en `_quarantine/` (no cuentan): track13_fix_bug_sin_codigo.json.

«Ejecutable» = `fill_blank_exec`, `fix_bug`, `sql_exec`, `js_exec`, `interactive`.
«Con código» = eso más `code_output`.

## Tabla

| Track | Nombre | Estado | Skills | Preguntas | Ejecutables | Con código | Lecciones | Mediana palabras/lección | Términos | Reservadas |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| track01 | Python Básico | construido | 52 | 870 | 139 | 466 | 52 | 213 | 52 | 0 |
| track02 | Python Intermedio | construido | 24 | 405 | 65 | 194 | 24 | 222 | 43 | 0 |
| track03 | Python Avanzado | construido | 24 | 397 | 53 | 151 | 24 | 230 | 41 | 0 |
| track04 | Ingeniería de Software | construido | 30 | 498 | 48 | 102 | 30 | 234 | 37 | 0 |
| track05 | Arquitectura de Software | construido | 24 | 365 | 0 | 33 | 24 | 183 | 42 | 0 |
| track06 | Fundamentos de IA | construido | 28 | 496 | 76 | 123 | 28 | 191 | 40 | 0 |
| track07 | Ingeniería de IA | construido | 25 | 481 | 78 | 103 | 25 | 187 | 39 | 0 |
| track08 | AWS Certified Cloud Practitioner (CLF-C02) | construido | 19 | 444 | 0 | 0 | 19 | 273 | 42 | 96 |
| track09 | PCEP – Python Entry-Level Programmer | construido | 15 | 269 | 42 | 42 | 15 | 168 | 40 | 2 |
| track10 | AWS Solutions Architect Associate (SAA-C03) | construido | 25 | 377 | 0 | 0 | 25 | 204 | 42 | 2 |
| track11 | AWS AI Practitioner (AIF-C01) | construido | 15 | 341 | 0 | 0 | 15 | 192 | 40 | 116 |
| track12 | SQL | construido | 20 | 300 | 60 | 60 | 20 | 178 | 36 | 0 |
| track13 | Ciberseguridad | construido | 20 | 398 | 19 | 19 | 20 | 180 | 50 | 0 |
| track14 | JavaScript Frontend | construido | 24 | 355 | 16 | 16 | 24 | 214 | 40 | 0 |
| track15 | Linux y Shell | construido | 12 | 180 | 0 | 16 | 12 | 223 | 12 | 0 |
| track16 | Algoritmos y Estructuras | construido | 12 | 158 | 0 | 0 | 12 | 217 | 12 | 0 |
| track17 | Redes y Protocolos | construido | 12 | 180 | 0 | 0 | 12 | 224 | 12 | 0 |
| track18 | Docker y Kubernetes | construido | 20 | 300 | 0 | 0 | 20 | 267 | 44 | 0 |
| track19 | Infraestructura como Código y CI/CD | construido | 20 | 300 | 0 | 0 | 20 | 217 | 0 | 0 |
| track20 | Ingeniería de Datos | construido | 20 | 300 | 0 | 0 | 20 | 227 | 42 | 0 |
| track21 | Ciencia de Datos | construido | 20 | 300 | 0 | 0 | 20 | 233 | 45 | 0 |
| track22 | Microsoft Azure | construido | 20 | 300 | 0 | 0 | 20 | 234 | 0 | 0 |
| track23 | Google Cloud Platform | construido | 20 | 300 | 0 | 0 | 20 | 247 | 54 | 0 |
| track24 | en cuarentena | cuarentena | 20 | 400 | 80 | 80 | 0 | 0 | 0 | 0 |
| track25 | en cuarentena | cuarentena | 20 | 400 | 80 | 80 | 0 | 0 | 0 | 0 |
| track26 | Git y Herramientas de Desarrollo | construido | 20 | 300 | 0 | 0 | 20 | 205 | 0 | 0 |
| track27 | Bases de Datos NoSQL | construido | 20 | 300 | 0 | 0 | 20 | 222 | 41 | 0 |
| track28 | Desarrollo Backend con FastAPI y Node.js | construido | 20 | 300 | 0 | 0 | 20 | 216 | 0 | 0 |
| track29 | QA y Testing | construido | 20 | 300 | 0 | 0 | 20 | 201 | 0 | 0 |
| track30 | Agile y Gestión de Producto | construido | 20 | 300 | 0 | 0 | 20 | 202 | 0 | 0 |
| track31 | Móvil (Android/Kotlin · iOS/Swift · Flutter/RN) | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track32 | Solana / Web3 | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track33 | Java / JVM | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track34 | C# / .NET | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track35 | Go | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track36 | Rust | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track37 | C / C++ y sistemas | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track38 | TypeScript avanzado | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track39 | SRE y observabilidad | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track40 | ISC2 CC — Certified in Cybersecurity | construido | 23 | 374 | 8 | 8 | 23 | 179 | 50 | 0 |
| track41 | PCAP — Python Certified Associate Programmer | construido | 16 | 300 | 0 | 36 | 16 | 217 | 30 | 0 |
| track42 | CompTIA Security+ (SY0-701) | construido | 20 | 300 | 0 | 0 | 20 | 241 | 42 | 0 |
| track43 | AWS Machine Learning Engineer Associate (MLA-C01; último día en inglés 28-09-2026, lo sustituye MLA-C02; GenAI/RAG/agentes ampliados) | construido | 27 | 334 | 5 | 5 | 27 | 236 | 30 | 3 |
| track44 | Microsoft Azure Fundamentals (AZ-900) | construido | 15 | 295 | 0 | 0 | 15 | 235 | 20 | 0 |
| track45 | Microsoft Azure AI Fundamentals (AI-901; sustituye a AI-900, retirado el 30-06-2026) | construido | 12 | 316 | 3 | 3 | 12 | 239 | 20 | 0 |
| track46 | Microsoft Azure Data Fundamentals (DP-900) | construido | 16 | 304 | 0 | 0 | 16 | 265 | 20 | 0 |
| track47 | Administración Windows / PowerShell | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track48 | PHP (Laravel, WordPress) | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track49 | Ruby (Rails) | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track50 | R para datos | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track51 | MLOps y despliegue de modelos | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track52 | Solidity / EVM | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track53 | Desarrollo de videojuegos (Godot, Unity) | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track54 | Embebidos e IoT | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track55 | Matemáticas para CS | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| track56 | Soporte IT y hardware | planificado | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Guardas existentes

- `scripts/check_question_bank.py`: rc=0 · [bank] PASS - ids unique, both languages present, options well formed, no position skew

Ninguna guarda da veredicto por track; su resultado es global.
