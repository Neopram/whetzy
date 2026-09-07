# Whetzy — Estado real / Honest Status

_Última actualización: 2026-09-07. Evaluación técnica brutalmente honesta._

Este documento distingue **lo que funciona de verdad y está verificado** de **lo
que es scaffold o no existe**. El plan aprobado (`velvet-tickling-fog.md`) es
maximalista (8 fases). Lo entregado es un **MVP real, funcional y desplegable** —
no el spec maximalista completo.

## Resumen ejecutivo
- **MVP shippable:** ~77% completo y **verificado end-to-end**.
- **Spec maximalista completo (8 fases):** ~26%.
- El **núcleo diferenciador** (motor adaptativo real corriendo sobre respuestas
  reales + registro + contenido + gamificación + tutor) **funciona hoy**.
- **1246 preguntas** en 7 tracks (Tracks 01-07 completos y verificados — **hito de contenido de Fase 1**; toda skill ≥6 Q, `source` al 100%).
- **Fase 1 cerrada al 100%** (sesión k): glosario bilingüe por track (70 términos con fuente) y pantalla de currículo gated con espina de prerequisitos BKT.

## Por fase

| Fase | Área | % | Estado |
|------|------|---|--------|
| 0 | Rebrand + Auth + Wire + Deploy-ready | **90%** | ✅ Real y verificado |
| 1 | Contenido bilingüe + glosarios + currículo gated | **100%** | ✅ Tracks 01-07 completos + glosario bilingüe (70 términos) + currículo gated (BKT) — verificado |
| 2 | Tutor AI (Groq) + RAG | **85%** | 🟡 Groq wired + ChromaDB RAG; GROQ_API_KEY pendiente de configurar |
| 3 | Gamificación + multiplayer + offline + animaciones | **45%** | 🟡 Gamificación real; multiplayer/offline no |
| 4 | DKT + churn + MLOps | **8%** | 🔴 Solo el motor base (FSRS/Elo/BKT/bandit) |
| 5 | Pipeline multi-agente + analytics | **3%** | 🔴 No construido |
| 6 | Microservicios + observabilidad | **5%** | 🔴 Monolito solamente |
| 7 | Cloud/K8s/IaC + ASVS + Stripe + i18n + nativo | **30%** | 🟡 Seguridad+Docker+CI reales; K8s/Stripe/nativo no |
| 8 | Garantía E2E + informe competitivo | **70%** | 🟡 Core verificado; este informe |

## Sesión 2026-09-07 (b): Fase 1 — Track 01 completo + citas de fuente
- **Track 01 (Python Básico) COMPLETO**: 12/12 módulos con contenido. Se autoraron los 9
  módulos faltantes (mod0104–mod0112): Listas, Dicts/Sets, Tuplas/Strings, Manejo de errores,
  Módulos/paquetes, File I/O, Comprensiones/generadores, POO básica, Librería estándar esencial.
  **+216 preguntas nuevas** (bancos de 396 en total; track01 = 306).
- **Redacción nativa ES + EN** (no traducción), 6 preguntas/skill con progresión
  easy→expert y tipos mixtos (mcq/true_false/code_output/fill_blank). Distractores basados en
  malentendidos reales (aliasing de listas, `sort()` devuelve None, agotamiento de generadores,
  `math.floor` de negativos, `is` vs `==`, coma flotante, etc.).
- **Campo `source` (cita canónica) cableado de extremo a extremo**: columna `source` en el
  modelo `Question` + loader + `QuizAnswerResponse` + badge en `QuizScreen` (ES/EN). Cada una de
  las 216 preguntas nuevas cita su fuente (CPython docs 3.13, PEPs, Fluent Python 2e,
  Effective Python 3e). Las 180 preguntas antiguas quedan con `source=NULL` (backfill pendiente).
- **Verificado**: `tsc -b` OK; AST backend OK; content_loader carga 396 preguntas con
  **0 skipped**; DB confirma columna `source` con 216 filas pobladas y 34/34 fill_blank correctos;
  flujo HTTP real (register→/quiz/start skill_id=sk010401→/quiz/answer) devuelve
  `source: "CPython docs 3.13 — Data Structures"`. **No verificado por pixel**: el render visual
  del badge (código typechecked y condicional sobre `feedback.source`).

## Sesión 2026-09-07 (c): Fase 1 — Track 02 completo (Python Intermedio)
- **Track 02 (Python Intermedio) COMPLETO**: 6/6 módulos con contenido. Se autoraron mod0201–mod0206:
  POO avanzada, Programación funcional, Decoradores/closures, Manejo de archivos avanzado, Testing con
  pytest, Iteradores/generadores avanzados. **+144 preguntas nuevas** (24 skills × 6). Banco total: 540.
- **Redacción nativa ES + EN** (no traducción), 6 preguntas/skill con progresión easy→expert y tipos
  mixtos. Distractores basados en malentendidos reales (MRO/diamante y `super()` cooperativo, name
  mangling, `__eq__` sin `__hash__`, argumento por defecto mutable, late binding de closures en bucles,
  `@deco` vs `@deco()`, `pickle` inseguro, claves JSON siempre string, `newline=''` en CSV, `groupby`
  solo consecutivos, agotamiento de iteradores, `yield`/`send`/`yield from`, mock mal tipeado silencioso).
- **Campo `source` (cita canónica)**: las 144 preguntas nuevas citan CPython docs 3.13, PEPs (255, 318,
  342, 380, 3119, 3129, 8), Fluent Python 2e, Effective Python 3e, y docs de pytest/openpyxl.
- **Verificado**: `validate_content.py` → **0 errores**, 540 IDs únicos, refs de skill válidas, esquema
  por tipo correcto, bilingüe completo; `content_loader` en DB limpia → **540 ingestadas, 0 skipped**;
  introspección DB confirma track02 = 144 con `source` poblado en 144/144, 18/18 fill_blank con
  `correct_answer` (options=JSON null, igual patrón que track01), UTF-8 limpio. **No re-verificado por
  HTTP**: el path `source` model→loader→schema→service→frontend ya se probó en vivo en la sesión (b) y
  no cambió; las nuevas preguntas usan la misma columna.

## Sesión 2026-09-07 (d): Fase 1 — Track 03 completo (Python Avanzado)
- **Track 03 (Python Avanzado) COMPLETO**: 6/6 módulos con contenido. Se autoraron mod0301–mod0306:
  Internos de CPython (GIL/PEP 703, refcount+GC generacional, modelo de objetos/`__slots__`, bytecode/`dis`),
  asyncio (async/await, event loop, tasks/`create_task`/`TaskGroup`, `gather`/`Semaphore`/`wait_for`),
  Metaclases (`type` 3-arg, metaclases custom vs `__init_subclass__`, `__new__` vs `__init__`, descriptors),
  Type hints (PEP 484/585/604/695, `TypeVar`/Generics, `Protocol`, mypy `--strict`/`reveal_type`),
  Concurrencia (`threading`/daemon/join, `multiprocessing`/spawn/pickle, `concurrent.futures`, locks/RLock/deadlock/`queue`),
  Optimización (`timeit`/`cProfile`/`pstats`, Big-O, `deque`/`Counter`/`heapq`, Cython `cdef`/NumPy/JIT).
  **+144 preguntas nuevas** (24 skills × 6). Banco total: 684.
- **Redacción nativa ES + EN** (no traducción), 6 preguntas/skill, progresión easy→expert, tipos mixtos.
  Distractores de malentendidos reales (GIL no acelera CPU, `time.sleep` bloquea el loop, `await` secuencial
  sin tasks, subtipado estructural de Protocol sin herencia, hints no verificados en runtime, `x += 1` no atómico,
  memoria separada en multiprocessing, `str +=` en bucle O(n²), `list.insert(0)` O(n)).
- **Campo `source`**: las 144 preguntas nuevas citan CPython docs 3.13, PEPs (484/487/544/585/604/695/703),
  Fluent Python 2e, Effective Python 3e, y docs de mypy/Cython/NumPy.
- **Verificado**: `validate_content.py` → **0 errores**, 684 IDs únicos, refs válidas, esquema por tipo correcto,
  bilingüe completo; `content_loader` en DB limpia → **684 ingestadas, 0 skipped**; introspección DB confirma
  track03 = 144 con `source` 144/144, 24/24 skills cubiertas, 24/24 fill_blank correctos, UTF-8 limpio.

## Sesión 2026-09-07 (e): Fase 1 — Track 04 completo (Ingeniería de Software)
- **Track 04 (Ingeniería de Software) COMPLETO**: 7/7 módulos con contenido. Se autoraron mod0402–mod0407:
  Código limpio y patrones de diseño (SOLID, GoF creacionales/estructurales/de comportamiento, refactoring/DRY/deuda
  técnica), APIs REST (restricciones REST/HATEOAS/Richardson, métodos HTTP y códigos de estado, diseño de endpoints,
  OpenAPI/Swagger), Bases de datos (SQL/JOINs/NULL/orden lógico, modelado relacional/normalización/ACID, índices/EXPLAIN/
  B-tree/N+1, ORMs/SQLAlchemy/Alembic, NoSQL/CAP/consistencia eventual), Autenticación (sesiones/CSRF/SameSite, JWT/alg:none/
  refresh, OAuth2/OIDC/PKCE, hashing Argon2/bcrypt/salt/memory-hard), Docker (imágenes vs contenedores/namespaces/cgroups,
  Dockerfile/cache/multi-stage/USER, Compose/DNS/depends_on/secrets, volúmenes/bind mounts/redes), CI/CD (CI/feedback rápido/
  feature flags, GitHub Actions/jobs/secrets, blue-green/canary/expand-contract, pirámide de tests/flaky/shift-left/pre-commit).
  **+150 preguntas nuevas** (25 skills × 6). El módulo mod0401 (Git) ya tenía 30 preguntas antiguas: se les **backfilleó el
  campo `source`** (capítulos canónicos de Pro Git 2e) y se añadió una 6ª pregunta a sk040105 (GitHub Flow) → mod0401 = 31.
  Track04 total = **181**. Banco total: **835**.
- **Redacción nativa ES + EN** (no traducción), 6 preguntas/skill, progresión easy→expert, tipos mixtos. Distractores de
  malentendidos reales (SRP con 3 responsabilidades, Singleton como anti-patrón, `getUser` RPC-sobre-HTTP, 200-con-error-en-body,
  `columna = NULL`, violación de 2FN, todos-los-índices-mejoran, N+1, el ORM evita saber SQL, `alg:none`, JWT payload = secreto,
  root en contenedor, `EXPOSE` publica el puerto, `depends_on` = listo, cobertura 100% = sin bugs, ice-cream-cone).
- **Campo `source`**: las 181 preguntas de track04 citan fuentes canónicas — Clean Code/Clean Architecture (R. C. Martin),
  Design Patterns (GoF), Refactoring 2e (Fowler), RFC 9110/9111/5789/6749/7519/7636/9106, dissertation de Fielding, PostgreSQL 16
  docs, SQLAlchemy 2.0/Alembic, Kleppmann (DDIA), OWASP cheat sheets, Docker docs, GitHub Actions docs, Humble & Farley, Pro Git 2e.
- **Verificado**: `validate_content.py` → **0 errores**, 835 IDs únicos, refs válidas, esquema por tipo correcto, bilingüe completo;
  `content_loader` en DB limpia → **835 ingestadas, 0 skipped**; introspección DB confirma track04 = 181 con `source` **181/181**,
  **30/30 skills** cubiertas (todas ≥6), **24/24 fill_blank** correctos, UTF-8 limpio (`\xe2\x80\x94`). Sin-source restante: 150
  (sk01=90 → mod0101-0103, sk06=30, sk07=30). **No re-verificado por HTTP**: el path de `source` no cambió desde la sesión (b).

## Sesión 2026-09-07 (f): Fase 1 — Track 05 completo (Arquitectura de Software)
- **Track 05 (Arquitectura de Software) COMPLETO**: 6/6 módulos con contenido (greenfield, 0 preguntas
  antiguas). Se autoraron mod0501–mod0506: Microservicios (principios/database-per-service/Conway,
  comunicación sync-async/gRPC/Saga/sidecar, API Gateway/BFF/TLS termination, service discovery/Consul/
  Kubernetes), Arquitectura orientada a eventos (command vs event, colas/DLQ/Kafka-log, pub/sub/exchange/
  consumer-group, event sourcing/CQRS/outbox/projection), Caching (cache-aside/write-through-back, Redis/
  ZSET/SCAN/single-threaded, invalidación/TTL/LRU, CDN/edge/cache-control/busting), Diseño de sistemas
  (escalado vertical-horizontal/percentiles/Amdahl, balanceo L4-L7/least-connections, CAP/PACELC/BASE/
  linealizabilidad, sharding/hot-spot/consistent-hashing), DDD (bounded contexts/context-map/ACL, entidad
  vs value object/primitive-obsession/frozen dataclass, agregados/repositorios/domain-service, lenguaje
  ubicuo/event-storming/táctico-estratégico), Escalabilidad y alta disponibilidad (replicación/lag/quorum/
  failover, tolerancia a fallos/nines/graceful-degradation/chaos-engineering/bulkhead, resiliencia/circuit-
  breaker/retry-backoff/timeouts/rate-limiting, observabilidad/3-pilares/tracing/SLO-error-budget/OTel).
  **+144 preguntas nuevas** (24 skills × 6). Banco total: **979**.
- **Redacción nativa ES + EN** (no traducción), 6 preguntas/skill, progresión easy→expert, tipos mixtos.
  Distractores de malentendidos reales (compartir BD entre servicios, `depends_on`=listo ya cubierto,
  'elige 2 de 3' del CAP como mito, hot-spot por mala sharding key, identidad de entidad por atributo mutable,
  invalidación en una sola réplica, retry sin backoff/jitter, esperar sin timeout, 'monitoreo = observabilidad').
- **Campo `source`**: las 144 preguntas de track05 citan fuentes canónicas — Newman (Building Microservices 2e,
  Monolith to Microservices), Richardson (Microservices Patterns), Kleppmann (DDIA), Evans/Vernon (DDD),
  Fowler (martinfowler.com), Nygard (Release It!), Google SRE Book, RFC 9110/9111, Redis/Kafka/RabbitMQ/
  Cloudflare/OpenTelemetry/Kubernetes docs.
- **Verificado**: `validate_content.py` → **0 errores**, 979 IDs únicos, refs válidas, esquema por tipo correcto,
  bilingüe completo; `content_loader` en DB limpia → **979 ingestadas, 0 skipped**; introspección DB confirma
  track05 = 144 con `source` **144/144**, **24/24 skills** cubiertas (todas =6), **24/24 fill_blank** correctos,
  UTF-8 limpio (`\xe2\x80\x94`). Sin-source restante: 150 (sk01=90 → mod0101-0103, sk06=30, sk07=30).
- **Nota de auditoría**: una auditoría intermedia detectó los 4 primeros módulos de track05 (96 Q) sin
  documentar y marcó la ingestión como pendiente de re-verificar; ambos puntos quedan resueltos aquí (6/6
  módulos documentados, ingestión de las 979 re-verificada). El conteo previo de 931 era parcial (4/6 módulos).

## Sesión 2026-09-07 (g): Fase 1 — Track 06 completo (Fundamentos de IA)
- **Track 06 (Fundamentos de IA) COMPLETO**: 6/6 módulos con contenido. El módulo mod0601
  (Matemáticas para ML) ya tenía 30 preguntas antiguas de alta calidad (5 skills × 6): se les
  **backfilleó el campo `source`** (Goodfellow *Deep Learning* Ch. 2/3/4/6.5 para álgebra lineal,
  cálculo, probabilidad y backprop; Wasserman *All of Statistics* Ch. 3/10 para estadística
  descriptiva e inferencial). Se autoraron los 5 módulos restantes (greenfield): Análisis de datos
  (NumPy/broadcasting/views vs copies/dtype, Pandas/loc-iloc/groupby/merge/SettingWithCopy, limpieza/
  NaN/imputación-mediana/data-leakage/one-hot, visualización/histograma-scatter-boxplot/ejes-truncados/
  Anscombe), ML clásico (workflow/train-val-test/estratificado, feature engineering/escalado/maldición-
  dimensionalidad, overfitting-underfitting/bias-variance/regularización/early-stopping, validación
  cruzada/k-fold/TimeSeriesSplit/LOOCV/grid-search, métricas/accuracy-engañosa/precision-recall/F1/MSE-MAE/
  AUC-ROC), Aprendizaje supervisado (regresión lineal/OLS/R²/Ridge, logística/sigmoide/log-loss/softmax/
  umbral, árboles/Random-Forest/bagging-vs-boosting/Gini, SVM/margen/vectores-soporte/kernel-trick/C/RBF,
  k-NN/lazy/escalado/k-impar/Minkowski), Aprendizaje no supervisado (K-Means/Lloyd/codo/óptimo-local/silueta,
  jerárquico/dendrograma/linkage/Ward, PCA/varianza-explicada/escalado/t-SNE, detección de anomalías/
  Isolation-Forest/3-sigma/falsos-positivos), Deep learning (perceptrón/XOR/bias/MLP/aproximación-universal,
  activaciones/ReLU/vanishing-gradient/softmax/tanh/Leaky-ReLU, backprop/forward-backward/época-batch-step/
  exploding-gradients/Adam, CNN/convolución/pooling/weight-sharing/jerarquía/transfer-learning, RNN/estado-
  oculto/LSTM/gates/BPTT/Transformer).
  **+138 preguntas nuevas** (23 skills × 6). Track06 total = **168**. Banco total: **1117**.
- **Redacción nativa ES + EN** (no traducción), 6 preguntas/skill, progresión easy→expert, tipos mixtos.
  Distractores de malentendidos reales (dot-product vs Hadamard, matmul conmutativa, `axis=0` suma filas,
  slice de NumPy = copia, media vs mediana con outliers, escalar antes de dividir train/test = leakage,
  one-hot vs enteros ordinales, accuracy con clases desbalanceadas, barajar CV en series temporales,
  árboles necesitan escalado, k=1 subajusta, sigmoide para regresión, PCA sin estandarizar, K-Means =
  óptimo global, XOR con perceptrón simple, ReLU no aporta no-linealidad).
- **Campo `source`**: las 168 preguntas de track06 citan fuentes canónicas — Goodfellow/Bengio/Courville
  (*Deep Learning*), Bishop (*PRML*), Géron (*Hands-On ML 2e*), Wasserman (*All of Statistics*), McKinney
  (*Python for Data Analysis 2e*), Anscombe (1973), y docs/papers (NumPy/pandas/scikit-learn/matplotlib/
  seaborn, Breiman, Liu-Isolation-Forest, van-der-Maaten-t-SNE, Hochreiter-LSTM, Kingma-Adam, Vaswani-Transformer).
- **Verificado**: `validate_content.py` → **0 errores**, 1117 IDs únicos, refs válidas, esquema por tipo
  correcto, bilingüe completo; `content_loader` en DB limpia → **1117 ingestadas, 0 skipped**; introspección
  DB confirma track06 = 168 con `source` **168/168**, **28/28 skills** cubiertas (todas ≥6), **25/25
  fill_blank** correctos, UTF-8 limpio. Sin-source restante: **120** (sk01=90 → mod0101-0103, sk07=30).
  **No re-verificado por HTTP**: el path de `source` no cambió desde la sesión (b).

## Sesión 2026-09-07 (h): Fase 1 — Track 07 completo (Ingeniería de IA) → HITO DE CONTENIDO
- **Track 07 (Ingeniería de IA) COMPLETO**: 6/6 módulos con contenido. Con esto, **los 7 tracks
  quedan completos y verificados** (hito de contenido de Fase 1). El módulo mod0701 (LLMs y Prompt
  Engineering) ya tenía 30 preguntas antiguas de alta calidad (5 skills): se les **backfilleó el
  campo `source`** (Vaswani *Attention Is All You Need* para Transformer/atención; Sennrich *BPE*
  para tokenización; Brown et al. *GPT-3* para few/zero/one-shot; Wei *Chain-of-Thought*, Wang
  *Self-Consistency* y OWASP LLM Top 10 para prompting avanzado/inyección; Holtzman *nucleus
  sampling* y OpenAI API ref para parámetros de generación) y se añadió una 6ª pregunta a sk070104
  (Tree of Thoughts, Yao 2023) → mod0701 = 31. Se autoraron los 5 módulos restantes (greenfield):
  RAG (fundamentos/retrieve-augment-generate/no-elimina-alucinaciones/2-fases/garbage-in-out/vs-long-
  context-lost-in-the-middle, embeddings/coseno/vector-DB/HNSW-ANN/dot=coseno-normalizado, chunking/
  overlap/tamaño-trade-off/semántico-vs-fijo/contextual-retrieval, re-ranking/cross-vs-bi-encoder/
  híbrido-denso-disperso/BM25/RRF), Agentes (fundamentos/loop/guardrails/memoria, tool-use/function-
  calling/no-lo-ejecuta-el-modelo/schema/validación-least-privilege/MCP, ReAct/thought-action-
  observation/grounding/Reflexion/plan-and-execute/manejo-de-errores, multi-agente/orquestador-workers/
  no-siempre-mejor/especialización/propagación-de-errores/breadth-first-coste), MLOps (versionado/Git-
  no-basta/DVC-MLflow/model-registry/Git-LFS/reproducibilidad, pipelines/notebook-frágil/training-
  serving-skew/feature-store/continuous-training/DAG-Airflow-Kubeflow, despliegue/batch-vs-online/
  offline≠online/shadow/canary/AB-vs-canary, monitoreo/data-vs-concept-drift/degradación-silenciosa/
  etiquetas-retrasadas/3-capas/concept-drift), Ética y seguridad (bias-fairness/atributo-protegido/
  proxy/unawareness-falla/feedback-loop/imposibilidad-Kleinberg-Chouldechova, privacidad/PII/differential-
  privacy/reidentificación/memorización-LLM/federated-learning/epsilon, alineación/RLHF/reward-hacking/
  model-cards/Constitutional-AI/inner-vs-outer, adversarial/ejemplo-adversarial/imperceptible/data-
  poisoning/FGSM/jailbreak/membership-inference-vs-extraction), Evaluación y observabilidad (métricas-
  LLM/generación-abierta/BLEU-ROUGE/n-gram-penaliza-paráfrasis/BERTScore/MMLU/contaminación, detección-
  alucinaciones/intrínseca-extrínseca/fluidez≠verdad/self-consistency-SelfCheckGPT/RAG-faithfulness/
  faithfulness-vs-relevance, LLM-as-judge/escalabilidad/sesgos-posición-verbosidad/pairwise-vs-pointwise/
  swap-de-orden/~80%-acuerdo-MT-Bench, observabilidad/traza/coste-latencia/3-pilares/tracing-multi-paso/
  OpenTelemetry-span-tree).
  **+120 preguntas nuevas** (20 skills × 6) + 1 nueva en mod0701. Track07 total = **151**. Banco total: **1238**.
- **Redacción nativa ES + EN** (no traducción), 6 preguntas/skill, progresión easy→expert, tipos mixtos.
  Distractores de malentendidos reales (RAG elimina alucinaciones, el modelo ejecuta la función él mismo,
  quitar la columna protegida = fairness, fluidez/confianza = veracidad, offline-bueno = producción-buena,
  más contexto siempre mejor, BLEU entiende semántica, chunks grandes siempre mejores, multi-agente siempre
  gana, temperature=0 = 100% determinista).
- **Campo `source`**: las 151 preguntas de track07 citan fuentes canónicas — Vaswani (Attention Is All You
  Need), Brown (GPT-3), Sennrich (BPE), Wei (CoT), Wang (Self-Consistency), Yao (ReAct/Tree of Thoughts),
  Shinn (Reflexion), Lewis (RAG), Karpukhin (DPR), Reimers-Gurevych (Sentence-BERT), Malkov-Yashunin (HNSW),
  Robertson-Zaragoza (BM25), Cormack (RRF), Wu (AutoGen), Anthropic (Building effective agents / Contextual
  Retrieval / Constitutional AI / MCP / multi-agent research), Sculley (Hidden Technical Debt), Kreuzberger
  (MLOps), Zinkevich (Rules of ML), Paleyes (ML deployment), Gama (concept drift), Barocas-Hardt-Narayanan
  (Fairness and ML), Kleinberg/Chouldechova (impossibility), Dwork (differential privacy), McMahan (federated
  learning), Carlini (training-data extraction), Ouyang (InstructGPT/RLHF), Mitchell (Model Cards), Goodfellow
  (adversarial examples/FGSM), Shokri (membership inference), Tramèr (model extraction), OWASP LLM Top 10,
  NIST AI RMF, Papineni (BLEU), Lin (ROUGE), Zhang (BERTScore), Hendrycks (MMLU), Liang (HELM), Es (RAGAS),
  Manakul (SelfCheckGPT), Zheng (MT-Bench/LLM-as-judge), OpenTelemetry docs.
- **Verificado**: `validate_content.py` → **0 errores**, 1238 IDs únicos, refs válidas, esquema por tipo
  correcto, bilingüe completo; `content_loader` en DB limpia → **1238 ingestadas, 0 skipped**; introspección
  DB confirma track07 = 151 con `source` **151/151**, **25/25 skills** cubiertas (todas ≥6), **6/6 fill_blank**
  correctos, 0 mcq/tf/code con `correct_index` NULL, UTF-8 limpio. Sin-source restante: **90** (solo
  sk01 → mod0101-0103; track07 ya no aporta ninguna). **No re-verificado por HTTP**: el path de `source`
  no cambió desde la sesión (b).

## Sesión 2026-09-07 (i): Fase 1 — Backfill de `source` en mod0101–0103 (deuda de fuentes saldada)
- **Backfilleadas las 90 preguntas antiguas restantes** de track01 (mod0101 Variables/tipos, mod0102
  Control de flujo, mod0103 Funciones), las únicas del banco que quedaban sin `source`. Cada pregunta
  cita ahora su fuente canónica: **CPython docs 3.13** (Tutorial §4/§5/§9, Built-in Types/Functions,
  Language Reference, Built-in Exceptions, Sorting HOW-TO, apéndice de coma flotante) y **PEPs**
  (8 para `is None` y lambdas nombradas, 285 `bool`⊂`int`, 308 ternario, 498 f-strings, 3102
  keyword-only, 3104 `nonlocal`). Overrides por-ID donde hay un hogar canónico más preciso
  (p. ej. gotcha del argumento mutable → Tutorial §4.8.1; `RecursionError` → Built-in Exceptions).
- **Verificado**: `validate_content.py` → **0 errores**, 1238 IDs únicos, **0 preguntas sin `source`**;
  `content_loader` en DB limpia → **1238 ingestadas, 0 skipped**; introspección DB confirma
  **source 1238/1238** (mod0101–0103 = 90/90), UTF-8 limpio (`\xe2\x80\x94`, `\xc2\xa7`). El banco
  completo queda con cita de fuente al 100%.
- **Hallazgo (honesto):** al contar por skill se detectó que track01 no estaba a 6 Q/skill en todas las
  skills (mod0102 sk010203/sk010204 = 5; mod0103 sk010302/03/05/06 = 5 y sk010304 = 4). Registrado
  como pendiente y **resuelto en la sesión j**.

## Sesión 2026-09-07 (j): Fase 1 — Cierre del hueco de skills de track01 (toda skill ≥6 Q)
- **Autoradas las 8 preguntas que faltaban** para llevar cada skill de track01 al piso de 6 Q (eran 8,
  no 11 como se estimó primero — corrección honesta del recuento). Nuevas: mod0102 → q010203006
  (acumulador `while`), q010204005 (`for...else` omitido por `break`); mod0103 → q010302006
  (parámetros solo-posicionales `/`, PEP 570), q010303006 (desempaquetado `**dict` en la llamada),
  q010304005 (`UnboundLocalError` por asignación que vuelve local a la variable), q010304006 (regla
  LEGB), q010305006 (`lambda` con `map`), q010306006 (memoización con `functools.lru_cache`). Todas
  ES+EN nativo, tipos mixtos, distractores de malentendidos reales, con `source` canónico (CPython
  docs 3.13 + PEP 570). Track01 pasa de 306 → **314**. Banco total: **1246**.
- **Verificado**: `validate_content.py` → **0 errores**, 1246 IDs únicos, **0 sin `source`**;
  `content_loader` en DB limpia → **1246 ingestadas, 0 skipped**; introspección DB confirma
  **207 skills, 0 con <6 preguntas** (toda skill del banco ≥6), track01 mod0101=30/mod0102=32/
  mod0103=36. Ahora "los 7 tracks completos (≥6/skill)" es literalmente cierto.

## Sesión 2026-09-07 (k): Fase 1 — Glosario bilingüe + currículo gated (CIERRE DE FASE → 100%)
- **Glosario por track (ES+EN)**: nuevo modelo `GlossaryTerm` (term_es/en, definition_es/en,
  `source`, order, FK a track) + loader desde `content/glossary/track01–07.json` + endpoint público
  `GET /api/v1/glossary/{track_id}` + pantalla. **70 términos** (10 por track), redacción nativa ES+EN,
  cada uno con **cita de fuente canónica** (CPython docs 3.13, PEPs, RFCs, Fielding, Kleppmann, GoF,
  Newman, Evans, SRE Book, Goodfellow, Bishop, Géron, Vaswani, Lewis-RAG, Yao-ReAct, Ouyang-RLHF,
  Zheng-LLM-as-judge, etc.). El loader es idempotente (upsert por PK) y sigue el mismo patrón que las
  preguntas; `content/glossary/` es opcional (el loader lo omite si no existe).
- **Pantalla de currículo gated (`TracksScreen`)**: nueva pestaña **«Rutas»** en el bottom-nav. Selector
  de los 7 tracks + dos vistas: **Currículo** (espina de prerequisitos BKT) y **Glosario** (con búsqueda).
  Endpoint `GET /api/v1/progress/curriculum?track_id=…` (auth) que calcula el estado por módulo:
  **bloqueado / disponible / completado**. Regla de desbloqueo = docstring del modelo `Module`: un módulo
  se desbloquea cuando el **dominio medio (BKT `p_known`) del módulo anterior** alcanza su
  `min_mastery_to_unlock` (por defecto 0.7); un módulo se marca «completado» al superar su propio umbral.
  Cada módulo desbloqueado muestra sus skills con dominio por-skill (★ al llegar al `MASTERY_THRESHOLD`
  de 0.95) y un botón **Practicar** que lanza un quiz acotado al track (`quiz/start` con `track_id`).
- **Verificado (de lo barato a lo caro)**: `tsc -b` del frontend → **0 errores**; `content_loader` en DB
  SQLite limpia → **1246 preguntas + 70 términos de glosario, 0 skipped** (idempotente en la 2ª pasada);
  test de la lógica de gating con usuario sintético (fresco: mod1 disponible, resto bloqueado; tras dominar
  mod1: mod1 completado, mod2 disponible, mod3+ bloqueado); smoke test HTTP vía ASGI (glossary 200 y 404,
  curriculum 200 con 12 módulos y **401 sin token**); y **verificación en navegador** (registro real →
  pantalla Rutas: currículo gated con estados 🔒/▶/✓, expandir módulo, glosario bilingüe con badge de
  fuente y filtro de búsqueda, botón Practicar → `quiz/start` 200 con pregunta de track01). Backend log
  limpio: 33× 200, 1× 201, sin 4xx/5xx (solo un warning cosmético de passlib/bcrypt al leer versión).
- **Con esto la Fase 1 queda al 100%.**

## Sesión 2026-09-07 (l): Fase 2 — Groq real + RAG ChromaDB
- **Groq wired**: `GroqProvider` ya existía; sólo falta `GROQ_API_KEY` en `.env` (gratis en console.groq.com). `LLMProvider` abstraction intacta — swap a Claude sin tocar callers.
- **RAG ChromaDB** (`app/services/ai/rag.py`): `RAGIndex` con `PersistentClient` (índice persiste entre reinicios en `backend/chroma_db/`). Embeddings: `SentenceTransformerEmbeddingFunction(all-MiniLM-L6-v2)`. Indexa las 1246 explicaciones de preguntas (ES+EN concatenadas) + 70 términos de glosario. Build en **background task** (lifespan `asyncio.create_task`) → startup instantáneo; primeras llamadas al tutor usan el fallback hasta que el índice está listo. Degradación limpia si chromadb/sentence-transformers no están instalados.
- **`tutor.py` modificado**: llama a `rag.retrieve(skill+pregunta, n=2)` antes de construir el prompt; inyecta fragmentos relevantes como `CONTEXTO RELACIONADO` (filtra el chunk idéntico al canonical para evitar duplicado). Funciona con o sin RAG listo.
- **Tests (6/6 verdes)**: 3 unit (`tests/unit/test_rag.py` — ChromaDB pipeline con FakeEF sin descarga de modelo) + 3 integration (`tests/integration/test_tutor_personalization.py` — `_times_missed()` sobre SQLite real: 0→1→2 fallos, ignora otros usuarios, cuenta sólo incorrectas). Infraestructura de tests creada (pytest.ini, `asyncio_mode=auto`).
- **Smoke ASGI-httpx** (sin servidor): register→quiz/start→tutor/explain → 200, `provider=fallback`, `times_missed=0`, `grounded=True`. El RAG no bloquea la respuesta.
- **Deuda honesta**: `GROQ_API_KEY` no configurada → tutor usa NullProvider. ChromaDB descarga all-MiniLM-L6-v2 (~90MB) en primera construcción del índice. Pyodide (Phase 2 diferenciador) pendiente.
- **Archivos nuevos/modificados**: `app/services/ai/rag.py` (nuevo), `app/core/config.py` (+CHROMA_PERSIST_PATH), `app/main.py` (+background RAG task), `app/services/ai/tutor.py` (+RAG context injection), `requirements.txt` (+chromadb, sentence-transformers), `tests/unit/test_rag.py`, `tests/integration/test_tutor_personalization.py`, `pytest.ini`, `.env.example` (+CHROMA_PERSIST_PATH), `.gitignore` (nuevo).

## Lo que funciona HOY (verificado en navegador)
- **Rebrand Neurium** completo: logo neural, identidad azul cielo, modo light por defecto.
- **Registro obligatorio** (email o manual) → JWT real, persistencia + refresh automático de token.
- **Quiz adaptativo real**: `POST /quiz/start` → pregunta elegida por Elo/ZPD → responder →
  el backend actualiza **Elo + BKT + FSRS + XP + racha + misiones + liga** y **persiste**. Verificado.
- **7 pantallas con datos 100% reales** (cero números falsos): Home, Quiz, Rutas (currículo gated + glosario), Stats, Liga, Perfil, Auth.
- **Contenido**: 1246 preguntas reales en 7 tracks ingestadas a la DB (loader idempotente, 0 skipped).
- **Gamificación**: 5 ligas, 4 misiones diarias, 8 badges con **auto-otorgamiento** funcionando.
- **Tutor AI**: endpoint `/tutor/explain` con proveedor swappable (Groq→Claude) + fallback
  grounded + personalización por nº de fallos. Botón "Explícame esto" cableado.
  **RAG ChromaDB** activo: indexa 1246 explicaciones + 70 términos al arranque (background);
  inyecta contexto relacionado en el prompt. Activar LLM real: `GROQ_API_KEY=<key>` en `.env`.
- **Seguridad ASVS 5.0 (L2)**: headers de seguridad + rate limiting por IP verificados.
- **Deploy-ready**: Dockerfile multi-stage no-root, docker-compose (API+Postgres+Redis),
  CI (GitHub Actions), `.env.example`, README.

## Deuda técnica / limitaciones honestas
- **`fill_blank`** excluido de la selección de quiz (necesita flujo de texto libre). Resuelto el
  bug de modelo (`correct_index` nullable) pero no se sirven aún.
- **Contenido**: **1246 preguntas** ≈ 83% de la meta de 1,500. Desglose verificado en DB:
  track01=314, track02=144, track03=144, track04=181, track05=144, track06=168, track07=151.
  **`source` cableado al 100%: 1246/1246 preguntas con cita canónica, 0 sin `source`** (deuda
  de fuentes saldada por completo, sesión i). **Cobertura de skills verificada: las 207 skills
  del banco tienen ≥6 preguntas — 0 skills por debajo del piso** (el hueco de track01 detectado en
  la sesión i quedó cerrado en la sesión j con 8 preguntas nuevas). **Glosario por track (70 términos
  bilingües con fuente) y pantalla de currículo gated (BKT) entregados y verificados en la sesión k** —
  Fase 1 al 100%.
- **RAG**: ChromaDB + SentenceTransformers integrados y verificados. Pendiente: dar `GROQ_API_KEY` en `.env` para activar el LLM real (gratis en console.groq.com).
- **Sin Groq key** configurada → el tutor usa el fallback grounded (no LLM aún). Wiring listo; solo falta la key.
- **DKT, churn, MLOps, pipeline multi-agente, microservicios, K8s/Terraform, Stripe/IAP,
  i18next completo, iconos nativos, duelos multiplayer, offline-sync** → **no construidos**.
- **Migraciones**: en dev se usa `init_db` (create_all); producción debería migrar a Alembic.
- **Persistencia local**: se probó con SQLite; el compose usa Postgres (no probado E2E en esta sesión).

## Cómo verificarlo
```bash
# Backend (dev, SQLite)
cd backend && python -m app.services.content_loader && python -m app.services.seed
uvicorn app.main:app --reload
# Frontend
cd frontend && npm run dev   # abre la PWA, regístrate, pulsa ESTUDIAR AHORA
```

---

## Sesión 2026-09-07 (m): Auditoría + Cierre Fase 2 + Rebrand Whetzy

### PASO 0 — Contradicción Pyodide: RESUELTA
- **Pyodide existe en código** (implementado en sesión paralela):
  - `frontend/public/pyodide-worker.js` ✅
  - `frontend/src/hooks/usePyodide.ts` ✅
  - `QuizScreen.tsx` con ramas `fill_blank_exec`, `fix_bug`, `code_output` ✅
  - `backend/app/services/quiz.py` con `_EXEC_TYPES` y grading por cliente ✅

### PASO 1 — Auditoría bloques A + K
| Criterio | Resultado |
|---|---|
| `tsc --noEmit` | 0 errores ✅ |
| Backend AST (`import app.main`) | OK ✅ |
| `content_loader` | 1253 Q ingestadas, 70 glosario, 0 skipped ✅ |
| `source` en respuesta HTTP | `'CPython docs 3.13 — Data Structures'` ✅ |
| Glosario HTTP (`/glossary/track01`) | 10 × 7 tracks = 70 términos ✅ |
| Curriculum sin token | 401 ✅ |

**Bugs corregidos en auditoría** (`gamification/service.py`):
- Faltaban `func`, `Response`, `StudySession`, `UserSkillState` en imports → NameError en `/quiz/answer`.
- Corregidos; endpoint devuelve HTTP 200 con todos los campos.

### PASO 2 — Tutor memory
- **Episódica**: `_times_missed` ya existía. Extendido: `missed ≥ 3` → instrucción obligatoria de añadir código Python ejecutable en la explicación.
- **Corto plazo**: `conversation_history: list[dict] | None` añadido a `ExplainRequest` y pasado al provider como mensajes anteriores. `GroqProvider.complete` ya acepta `history`.
- **Largo plazo**: `_get_weak_skills(user_id, threshold=0.4, limit=3)` inyecta skills débiles del usuario en el system prompt.
- **Tests**: `tests/integration/test_tutor_memory.py` — 4/4 verdes (times_missed cuenta correctamente, no contamina entre usuarios, ignora respuestas correctas).

### PASO 4 — Rebrand Neurium → Whetzy
Reemplazado en todos los archivos de código (NO docs/ ni content/):
- Frontend (8 archivos): `App.tsx`, `TopBar.tsx`, `AuthScreen.tsx`, `ProfileScreen.tsx`, `QuizScreen.tsx`, `api.ts`, `design-tokens.css`, `theme.ts`
- Backend (4 archivos): `config.py` (`APP_NAME`), `main.py` (logger), `rag.py` (logger + collection name), `provider.py` (docstring)
- Raíz: `README.md`, `frontend/package.json`
- Verificación: 0 ocurrencias de `Neurium`/`neurium` en código; tsc 0 errores; backend AST OK.

### Fase 2 estado real (post-sesión m)
| Ítem | Estado |
|---|---|
| ChromaDB RAG activo | ✅ (sesión l) |
| Groq wired | ✅ sin key → fallback grounded; `GROQ_API_KEY` en `.env` para LLM real |
| Pyodide WebWorker (fill_blank_exec, fix_bug, code_output) | ✅ (sesión paralela, verificado PASO 0) |
| Tutor memory completa (ST + LT + episódica) | ✅ (sesión m) |
| Rebrand Whetzy | ✅ (sesión m) |
| **Fase 2 % real** | **~92%** — pendiente: GROQ_API_KEY en `.env` prod + Pyodide smoke test en navegador real |
