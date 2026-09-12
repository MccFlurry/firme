# Plan — Firme (Hackatón WIN Chiclayo 2026 · Reto 03)

Spec de origen: `/Users/mccflurry/Downloads/Prompt-Maestro-WIN-Reto03-v2.md` (prompt maestro v2).
Este plan traduce ese prompt a tareas por carril. Lo que el prompt fija, este plan no reabre.

## Objetivo

Un jurado abre una URL en su teléfono, pega un lote de ventas que nunca vimos, y el sistema
separa buenas de malas explicando **qué no coincide con qué** (promesa ↔ catálogo ↔ registro
↔ entregable), con costo esperado en soles, contrafáctico, confirmación del cliente por enlace
y bandeja de avisos. Nombre del producto: **Firme** (sin la marca WIN).

Encuadre obligatorio en toda copia de UI y docs: *protege las ventas buenas de quedar atrapadas
en revisión, protege al cliente de una promesa que no se sostiene, y protege al vendedor honesto
de cargar con el costo del que no lo es*. Nunca "policía del vendedor".

## Decisiones cerradas (no reabrir)

- **Stack:** Python 3.13, FastAPI + Jinja2 + CSS/JS vanilla (móvil primero), PyYAML, pydantic,
  pytest. Un solo proceso `uvicorn app.main:app`. Estado en `data/state.json` (`app/store.py`).
  Sin build step, sin frameworks JS, sin DB.
- **Intérprete:** siempre `.venv/bin/python` / `.venv/bin/pytest` (ya instalado).
- **Idioma:** UI en español neutro profesional. Código, identificadores, archivos y comentarios
  en inglés. Marca de agua `SIMULADO` visible en todas las pantallas.
- **Contrato congelado:** `contracts/types.py`. Entrypoints públicos del motor:
  - `engine.evaluate(sale: Sale, ctx: Context) -> Verdict`
  - `engine.ingest.parse(payload: str | bytes | list[dict], filename: str | None = None) -> tuple[list[Sale], IngestReport]`
  - `engine.llm.normalize_promise(text: str, catalog) -> tuple[Promise, LlmMode]`
- **Reglas, catálogo, costos y umbrales en `config/*.yaml`**, cada ítem con `origen:
  SUPUESTO_DEMO | PUBLICO` y `fuente`. Nunca en código. La UI muestra el origen junto a cada
  regla disparada.
- **Condiciones de reglas:** expresiones Python evaluadas con `eval` sobre un dict plano de
  `facts` y `__builtins__` vacío. Las reglas son config confiable, los datos solo son valores.
  Marcar con `# ponytail: eval on trusted YAML; swap for simpleeval if rules ever come from users`.
- **LLM opcional:** SDK `anthropic`, modelo `claude-opus-5`, `client.messages.parse(...,
  output_format=PromiseExtract, output_config={"effort": "low"}, max_tokens=1024)`, timeout 10 s.
  Sin `ANTHROPIC_API_KEY`, sin red o cualquier excepción → parser determinista y
  `llm_mode="determinista"` visible en pantalla. Verificar la firma de `parse` contra el SDK
  instalado (`.venv`, anthropic 1.5.0) antes de escribir.
- **Ventana:** `config/settings.yaml` → `install_window_hours: 48`, `confirmation_window_hours: 24`,
  `alert_buffer_hours: 12`. Toda la arquitectura se justifica contra esa ventana.
- **Sin auth** salvo el token del enlace de confirmación (`secrets.token_urlsafe(8)`).
- **Fuera de alcance (no construir):** auth, multiusuario, roles, telemetría, migraciones,
  paginación, modo oscuro, envío real de correo/WhatsApp, versionado de config, tests fuera del
  motor.

## El rombo — cuatro comparadores

| Arista (`Edge`) | Compara | Defecto que detecta |
|---|---|---|
| `promesa-catalogo` | promesa normalizada vs `catalog.yaml` | promete plan/velocidad/precio/promo/condición que no existe o no es combinable |
| `promesa-registro` | promesa vs campos registrados | lo dicho al cliente ≠ lo escrito (precio, plan, promo, fecha de instalación) |
| `catalogo-registro` | registro vs catálogo | precio bajo tarifa, promo no aplicable al plan, plan inexistente |
| `registro-entrega` | registro vs cobertura/instalación/facturación | zona sin cobertura para la tecnología, instalación fuera de ventana, monto a facturar ≠ registrado |
| `identidad` | consentimiento y titular | sin evidencia de consentimiento, colisión de teléfono/correo/DNI, cliente desconoce |
| `senal` | señales no obvias | temporales, reedición, cohorte, ausencia |

## Modelo de costo esperado (`config/costs.yaml`, todo `SUPUESTO_DEMO`)

```yaml
outcomes:
  instalacion_fallida: {cost: 120, label: "Instalación fallida", note: "camión + técnico + reprogramación"}
  reclamo:             {cost: 80,  label: "Reclamo", note: "atención + gestión + nota de crédito"}
  baja_temprana:       {cost: 350, label: "Baja temprana", note: "costo de adquisición perdido + equipo no recuperado"}
  reversion_facturacion: {cost: 60, label: "Reversión de facturación", note: "refacturación + conciliación"}
review: {cost: 15, minutes: 10, note: "10 min de analista de calidad a S/ 90/h"}
recoverability: 0.7          # fracción del costo esperado que una revisión a tiempo evita
thresholds:
  retain_multiple: 4         # E[costo] >= 4 × costo de revisión → RETENER
priors:                      # tasa histórica de defecto por canal, como calibración bayesiana
  call_center: 0.08
  campo: 0.12
  web: 0.04
  tienda: 0.03
  default: 0.06
prior_impacts: {reclamo: 0.5, baja_temprana: 0.3}   # cómo el prior se reparte en desenlaces
origen: SUPUESTO_DEMO
```

- `p(outcome) = 1 − Π(1 − p_i)` (noisy-OR) sobre `impacts` de cada evidencia disparada, más el
  prior del canal repartido por `prior_impacts` (prior × peso).
- `expected_cost = Σ p(o) × cost(o)`.
- Decisión: `ABSTENERSE` si faltan `plan` **y** `price`, o si no hay ningún identificador de
  cliente (`customer_doc`, `phone`, `email`) — explicar en `abstain_reason`. Si alguna evidencia
  es `bloqueante` → `RETENER`. Si `expected_cost >= retain_multiple × review.cost` → `RETENER`.
  Si `expected_cost >= review.cost` → `REVISAR`. Si no → `APROBAR`.
- `recoverable_per_minute = expected_cost × recoverability / review.minutes`. La cola de la
  bandeja se ordena por esto, no por score.
- El umbral no se elige a dedo: el corte es donde el costo esperado supera el costo de revisar.
  Decirlo en la UI en una línea.

## Señales no obvias (todas disparables desde el formulario)

1. **Temporal — ráfaga:** ≥3 ventas del mismo `seller_id` en 10 min (`facts.burst_count`).
   **Temporal — llenado:** `fill_seconds < 40` (`facts.fill_seconds`, medido en el navegador).
   **Temporal — hora:** `registered_at` entre 23:00 y 06:00 (`facts.hour`).
2. **Reedición:** `edits` con `field == "price"` ≥ 2 veces → alta; edición de `customer_name` o
   `customer_doc` después de enviar → media (`facts.price_edits`, `facts.identity_edits`).
3. **Colisión:** mismo `phone`/`email`/`customer_doc` en otra venta con distinto
   `customer_name` (`facts.phone_collisions`, ...); ≥2 ventas misma `address` normalizada el
   mismo día (`facts.address_collisions`).
4. **Lingüística:** `promise.claims` contiene ítems de `config/lexicon.yaml` marcados como
   inexistentes o insostenibles ("gratis para siempre", "sin contrato", "velocidad garantizada",
   "instalación hoy") (`facts.unsupported_claims`).
5. **Ausencia:** `consent_evidence` vacío; confirmación en `silencio`
   (`facts.consent_missing`, `facts.confirmation_status`).
6. **Cohorte:** prior por canal (arriba). Enmarcado como calibración, nunca sanción.

## Confirmación del cliente (`/confirm`)

- `POST /confirm/create/{sale_id}` → crea `Confirmation` (token, `expires_at = now +
  confirmation_window_hours`), registra evento, redirige a la vista de veredicto que muestra el
  enlace y un QR (generar QR con SVG inline sin dependencias, o mostrar solo el enlace corto).
- `GET /c/{token}` → pantalla del cliente en lenguaje llano: "Hola {nombre}. {vendedor} te
  ofreció: {plan} a S/ {precio}/mes {promo}. Instalación: {fecha}. ¿Es esto lo que acordaste?"
  Tres botones: **Sí, es lo que acordé** / **Quiero corregir algo** (textarea) / **No pedí este
  servicio**. Texto redactado con `engine.llm.explain_for_client` si hay LLM, plantilla si no.
- `POST /c/{token}` → actualiza `status` (`confirmada` | `corregida` | `desconocida`), evento,
  reevalúa la venta con `Context.confirmation` y guarda el nuevo veredicto.
- `POST /confirm/expire/{sale_id}` → botón "Simular vencimiento de ventana (demo)" → `silencio`
  y reevaluación. El silencio es la señal más fuerte del sistema después de "desconocida".
- Efecto en el motor (`facts.confirmation_status`): `confirmada` → las reglas de `identidad` y
  `promesa-registro` no disparan (`and confirmation_status != "confirmada"` en la condición);
  `corregida` → regla media `promesa-registro` con la nota del cliente; `desconocida` →
  bloqueante `identidad`; `silencio` → alta `identidad`.

## Capa de aviso (`/bandeja`)

Una pantalla, no un sistema de notificaciones. Cada veredicto `REVISAR`/`RETENER` genera un
`Alert`:

| Decisión | Destinatario | Urgencia | Plazo | Acción |
|---|---|---|---|---|
| RETENER | Despacho e instalaciones + Supervisor de ventas | alta | `install_date − alert_buffer_hours` | "No despachar. Verificar con el cliente por el enlace de confirmación." |
| REVISAR | Calidad de venta | media | `install_date − alert_buffer_hours` | "Llamar al cliente y validar {campo con evidencia más grave} antes del plazo." |

La bandeja agrupa por destinatario, ordena por `recoverable_per_minute` desc, muestra plazo
restante, y tiene botón "Hecho" (marca en `alerts_done`). Sin `install_date`: plazo = `now +
install_window_hours − alert_buffer_hours`.

## Contexto y archivos

```
contracts/types.py        # congelado (Fable)
app/store.py              # JSON + lock (Fable)
config/catalog.yaml       # planes, promos, cobertura por distrito, alias de nombres
config/rules.yaml         # reglas del rombo + señales
config/costs.yaml         # desenlaces, costos, umbrales, priors
config/lexicon.yaml       # frases de promesa insostenibles / inexistentes, alias de planes
config/settings.yaml      # ventanas y parámetros de señales
engine/__init__.py        # expone evaluate
engine/facts.py           # Sale + Context + catalog → dict plano de facts
engine/rules.py           # carga YAML, evalúa condiciones, arma Evidence
engine/cost.py            # noisy-OR, costo esperado, decisión, alert
engine/counterfactual.py  # aplica fixes de reglas hasta que la decisión sea APROBAR
engine/llm.py             # normalize_promise, explain_for_client (LLM → determinista)
engine/ingest.py          # mapeo aproximado, JSON/CSV/form, IngestReport
app/main.py               # FastAPI: rutas de venta, lote, veredicto, bandeja
app/templates/*.html      # base, home/form, verdict, batch, inbox
app/static/app.css, app.js
confirm/router.py         # APIRouter con /confirm/* y /c/{token}
confirm/templates/*.html  # client.html, done.html
data/cases.json           # 25 casos sintéticos etiquetados
tests/test_engine.py      # solo motor
docs/PREGUNTAS-MENTOR.md, docs/ENTREVISTA-VENDEDORES.md, docs/CONTEXTO.md, docs/GUION-DEMO.md
README.md, CONTRATO-DE-DATOS.md, LICENSE, Dockerfile, render.yaml, fly.toml
```

### Forma de `config/rules.yaml`

```yaml
- id: R03_precio_bajo_tarifa
  name: Precio registrado por debajo del tarifario
  edge: catalogo-registro
  description: El precio mensual registrado es menor que el del plan en el catálogo vigente.
  condition: "price is not None and catalog_price is not None and price < catalog_price * (1 - price_tolerance)"
  inputs: [price, catalog_price, price_tolerance]
  severity: alta
  strength: determinista
  message: "Precio registrado S/ {price} por debajo del tarifario S/ {catalog_price}."
  source: "Tarifario público (config/catalog.yaml)"
  origen: PUBLICO
  impacts: {reclamo: 0.35, reversion_facturacion: 0.4}
  fix: {field: price, value: catalog_price, reason: "igualar al tarifario vigente"}
```

`inputs` nombra las claves de `facts` que se copian a `Evidence.values`. `message` se formatea
con `str.format(**facts)`. `fix` es opcional: `value` es una clave de `facts` o un literal.

### Forma de `config/catalog.yaml`

```yaml
origen: SUPUESTO_DEMO      # o PUBLICO con fuente y fecha si se verifica en https://win.pe
fuente: "https://win.pe — verificar precios vigentes; los valores de este archivo son supuestos de demo"
plans:
  fibra_200: {name: "Fibra 200 Mbps", speed_mbps: 200, price: 79.90, tech: fibra, aliases: [fibra 200, 200 megas, plan 200]}
  fibra_400: {...}
  fibra_600: {...}
  fibra_1000: {...}
promos:
  primer_mes_gratis: {name: "Primer mes gratis", applies_to: [fibra_400, fibra_600, fibra_1000], months: 1}
  descuento_3m: {name: "S/ 20 de descuento por 3 meses", applies_to: [fibra_200, fibra_400], discount: 20, months: 3}
coverage:
  chiclayo_centro: {tech: [fibra], max_speed_mbps: 1000}
  la_victoria: {tech: [fibra], max_speed_mbps: 600}
  jose_leonardo_ortiz: {tech: [fibra], max_speed_mbps: 400}
  pimentel: {tech: [inalambrico], max_speed_mbps: 50}
  monsefu: {tech: [], max_speed_mbps: 0}
price_tolerance: 0.02
install_sla_days: 3
```

## Patrón de referencia

No existe código previo. `contracts/types.py` y este plan son el patrón. Para tareas de
opencode, el patrón de referencia es el archivo que se indica en cada tarea.

## Tareas

Orden: T1 ∥ T2 → T3 ∥ T5 → T3b ∥ T4 → T6 → T7. Fable commitea y etiqueta al cerrar cada fase.

### T1 · Motor + config + tests — carril `codex-worker` (gpt-6-astra, xhigh)
Por qué: sin patrón previo, es el corazón del producto y define semántica.

- [x] `config/{catalog,rules,costs,lexicon,settings}.yaml` con las formas de arriba. Mínimo 14
  reglas cubriendo las seis aristas y las seis señales. Cada regla con los ocho campos del
  prompt maestro (`id, name, description, condition, severity, message, source, origen`) más
  `edge, strength, inputs, impacts, fix`.
- [x] `engine/facts.py`: construye el dict plano de facts desde `Sale`, `Context` y catálogo
  (incluye `catalog_price`, `promo_applies`, `zone_supports_plan`, `zone_max_speed`,
  `install_within_window`, `burst_count`, `fill_seconds`, `hour`, `price_edits`,
  `identity_edits`, `phone_collisions`, `email_collisions`, `doc_collisions`,
  `address_collisions`, `consent_missing`, `confirmation_status`, `promise_*`,
  `unsupported_claims`, `price_tolerance`, `prior`). Normaliza direcciones (minúsculas, sin
  tildes, sin puntuación, colapsar espacios). Nunca lanza por campo faltante: `None`.
- [x] `engine/llm.py`: `normalize_promise(text, catalog) -> (Promise, LlmMode)` y
  `explain_for_client(sale, promise) -> (str, LlmMode)`. Determinista: regex de velocidad
  (`\d+\s*(mb|megas)`), precio (`S/\s*\d+`), alias de planes y promos del catálogo, claims del
  lexicon. LLM solo si `ANTHROPIC_API_KEY` está definido; cualquier excepción o timeout →
  determinista. Nunca bloquear la demo.
- [x] `engine/rules.py`, `engine/cost.py`, `engine/counterfactual.py`, `engine/__init__.py`
  con `evaluate(sale, ctx) -> Verdict` según las secciones de arriba. El contrafáctico aplica
  los `fix` de las evidencias en orden de severidad descendente, reevalúa tras cada uno, y se
  detiene en `APROBAR`; si ninguno alcanza, `text` lo dice ("ningún cambio de un solo campo
  la haría pasar; requiere confirmación del cliente").
- [x] `tests/test_engine.py` (pytest, sin fixtures elaboradas): una venta limpia → APROBAR;
  precio bajo tarifa → REVISAR con evidencia R03 y contrafáctico que la lleva a APROBAR;
  promesa con claim insostenible → evidencia lingüística; confirmación `desconocida` →
  RETENER; confirmación `confirmada` limpia identidad; ráfaga de 3 ventas → señal temporal;
  colisión de teléfono → señal; venta sin plan ni precio → ABSTENERSE; `normalize_promise`
  determinista extrae plan/precio/claims. Cada test debe fallar si se revierte la lógica.

### T2 · Documentos de Fase 0 + contrato de datos — carril `opencode-worker` (deepseek-v4-pro)
Por qué: es escritura contra una especificación cerrada, no diseño.

- [x] `docs/PREGUNTAS-MENTOR.md`: máximo 12 preguntas priorizadas al mentor comercial, cada
  una con *qué decidimos con la respuesta*. Deben apuntar a lo que el diseño asume:
  ventana venta→instalación real, cómo se registra hoy la promesa, cómo se valida titularidad,
  tasa de instalaciones fallidas por canal, costo real de cada desenlace, qué campos existen en
  el registro, quién recibe hoy los avisos, cuánto tarda una revisión.
- [x] `docs/ENTREVISTA-VENDEDORES.md`: 8 preguntas para descubrir cómo se rompe la promesa en
  la práctica y qué atajos existen (sin tono de auditoría; el vendedor honesto es aliado).
- [x] `docs/CONTEXTO.md` con las 7 secciones del prompt maestro (§9.1), estado inicial
  "en construcción", *Decisiones cerradas* copiadas de este plan, *Supuestos sin confirmar*
  (todo `SUPUESTO_DEMO` del catálogo y costos), apartado *Aprendizajes del mentor* vacío con
  plantilla, y apartado *Dudas de diseño* vacío.
- [x] `CONTRATO-DE-DATOS.md` en la raíz, nivel producción, según §8 del prompt maestro: tabla
  con las 8 columnas por campo (los campos son los de `contracts/types.py::Sale` más los que
  el arco requiere: resultado de instalación, primera factura, baja en 90 días como etiquetas),
  mecanismo de entrega por campo (API / webhook / lote nocturno / CDC), modo de degradación
  por campo ausente (qué señales dejan de calcularse, si se abstiene), minimización de datos
  personales (qué no pedimos pudiendo pedirlo: nombre completo → iniciales, dirección →
  hash normalizado, DNI → hash), *qué debería exponer WIN internamente y hoy probablemente
  no* redactado como recomendación de arquitectura de información, y *qué funciona en el día
  uno sin nada de WIN* vs *qué requiere integración*.
- Restricción dura en todos los documentos: jamás proponer cambios de precio, comisión o
  incentivos. Nunca presentar un dato sintético como real. Lenguaje: español neutro
  profesional.

### T3 · Aplicación web: rebanada vertical + despliegue — carril `codex-worker` (gpt-6-astra, xhigh)
Por qué: integra motor, UI móvil y despliegue sin patrón previo. Depende de T1.

- [x] `app/main.py` (FastAPI, Jinja2, static). Rutas:
  - `GET /` formulario de venta (móvil primero) con `promise_text` en lenguaje natural, campos
    de `Sale`, selector de canal/distrito/plan/promo desde el catálogo, `fill_seconds` medido
    en JS desde el primer foco, y ejemplo precargable con un botón "Cargar ejemplo".
  - `POST /ventas` → crea `Sale` (id `V-XXXX`), normaliza promesa, evalúa con `Context`
    (historial = ventas guardadas), guarda venta + veredicto + evento, redirige a
    `GET /ventas/{id}`.
  - `GET /ventas/{id}` veredicto: decisión grande, costo esperado descompuesto por desenlace
    (p × costo), severidad × fuerza, cadena de evidencia completa (regla, condición literal,
    valores, fuente, `origen` como etiqueta junto a cada regla), contrafáctico, campos
    faltantes, `llm_mode` ("Capa LLM: activa" / "Capa LLM: no disponible, comparador
    determinista"), promesa normalizada, eventos, botón "Editar" y bloque de confirmación:
    botón `POST /confirm/create/{id}`, enlace y estado si existe, botón
    `POST /confirm/expire/{id}` (demo). Los botones de confirmación se renderizan aunque el
    router de T4 aún no exista (T4 los provee).
  - `GET /ventas/{id}/editar` y `POST /ventas/{id}/editar`: formulario prellenado; cada campo
    cambiado agrega un `FieldEdit` y reevalúa (alimenta la señal de reedición).
  - `GET /bandeja` bandeja de avisos según la sección "Capa de aviso"; `POST /bandeja/{sale_id}/hecho`.
  - `GET /salud` → `{"ok": true, "llm": "..."}`.
  - `app.include_router(confirm_router)` importando `from confirm.router import router as
    confirm_router` dentro de un `try/except ImportError` con un router vacío de reemplazo
    hasta que T4 exista.
- [x] `app/templates/base.html`: cabecera con nombre **Firme**, subtítulo "Que lo
  prometido sea lo entregado", marca de agua `SIMULADO` fija, navegación (Nueva venta · Lote ·
  Bandeja), pie con el encuadre. `app/static/app.css` ≤ 200 líneas, móvil primero, tipografía
  del sistema, colores de decisión (APROBAR verde, REVISAR ámbar, RETENER rojo, ABSTENERSE
  gris). `app/static/app.js`: cronómetro de llenado, "Cargar ejemplo", copiar enlace.
- [x] `Dockerfile` (python:3.13-slim, `pip install -r requirements.txt`, `uvicorn app.main:app
  --host 0.0.0.0 --port ${PORT:-8000}`), `render.yaml` (web service free, Docker),
  `fly.toml` mínimo. Sin secretos.
- [x] Verificar con `.venv/bin/uvicorn app.main:app --port 8765` + `curl` que `/`, `POST
  /ventas` y `/ventas/{id}` responden 200 y que el veredicto muestra evidencia y contrafáctico.

### T3b · Ingesta tolerante + vista de lote — carril `opencode-worker` (deepseek-v4-pro)
Por qué: algoritmo especificado, con `app/main.py` y `app/templates/verdict.html` como patrón.
Depende de T3.

- [x] `engine/ingest.py`: acepta JSON (lista de objetos o `{"ventas": [...]}`), CSV (con
  `csv.Sniffer`), o lista de dicts. Mapea columnas a campos de `Sale` con un diccionario de
  sinónimos (es/en, con y sin tildes, snake/camel) y `difflib.get_close_matches(cutoff=0.75)`.
  Reporta `mapped`, `unrecognized` (van a `Sale.extra`), `missing`. Filas con error se
  reportan en `errors` y se omiten; **nunca lanza**. Etiquetas: cualquier columna
  `label|etiqueta|resultado|es_buena|fraude` normalizada a `buena|mala`.
- [x] `GET /lote`: textarea para pegar, `input type=file`, ejemplo listo para pegar (5 filas
  con esquema *distinto* al nuestro), botón "Cargar los 25 casos de demo" (`data/cases.json`).
  `POST /lote`: evalúa cada fila con historial = filas del lote + ventas guardadas, guarda
  todo, muestra el `IngestReport` (mapeo, no reconocidos, faltantes, errores), tabla ordenada
  por `recoverable_per_minute` con decisión, costo, regla principal, enlace al veredicto; y
  si hay etiquetas, matriz de confusión 2×2 (positivo = decisión ∈ {REVISAR, RETENER};
  ABSTENERSE se cuenta aparte) con precisión y exhaustividad.
- [x] Tests en `tests/test_ingest.py`: esquema desconocido con columnas en inglés y con
  tildes mapea `plan`, `precio`, `telefono`; columna basura va a `unrecognized`; CSV y JSON
  dan el mismo resultado; una fila corrupta no tumba el lote.

### T4 · Confirmación del cliente — carril `opencode-worker` (deepseek-v4-pro)
Por qué: rutas y efecto ya especificados; patrón `app/main.py` + `app/templates/base.html`.
Depende de T3.

- [x] `confirm/router.py` con las rutas de la sección "Confirmación del cliente";
  `confirm/service.py` con `create(sale_id)`, `respond(token, status, note)`,
  `expire(sale_id)`, `get(sale_id)`; reevaluación reutilizando la función de evaluación de
  `app/main.py` (extraerla a `app/services.py::evaluate_and_store(sale)` si aún no existe,
  cambio mínimo). Plantillas `confirm/templates/client.html` (sin navegación interna, solo la
  promesa en lenguaje llano, tres botones grandes, marca `SIMULADO`) y `done.html`.
- [x] Eventos: `enlace_generado`, `confirmada`, `corregida`, `desconocida`, `silencio`.
- [x] Verificar de punta a punta con curl: crear venta → crear enlace → `GET /c/{token}` 200 →
  `POST` con `desconocida` → el veredicto de la venta pasa a `RETENER`; `confirmada` → baja el
  costo esperado.

### T5 · 25 casos sintéticos etiquetados — carril `opencode-worker` (kimi-k3)
Por qué: datos contra una especificación; patrón `contracts/types.py` y `config/rules.yaml`.
Depende de T1.

- [x] `data/cases.json`: lista de 25 objetos con esquema `Sale` (sin `promise`, sí
  `promise_text`), todos con `label`, distribución aproximada: 10 buenas, 10 malas, 5
  ambiguas/límite. Cada caso mal etiquetado dispara al menos una regla concreta de
  `config/rules.yaml` (anotar en un campo `extra.nota_demo` qué regla debe disparar). Incluir:
  ráfaga de 3 ventas de un vendedor en 8 minutos, colisión de teléfono, dirección repetida,
  promesa con claim insostenible, promo no aplicable, zona sin cobertura para el plan, sin
  consentimiento, precio bajo tarifa, reedición de precio, llenado en 20 s, registro a las
  02:40, y ventas buenas en todos los canales. Nombres, DNI (8 dígitos), teléfonos (9 dígitos,
  empiezan en 9) y correos generados; nada real. Marcar `extra.simulado: true` en todos.
- [x] Verificar con `.venv/bin/python -c` que los 25 cargan como `Sale` y que
  `engine.evaluate` sobre los 25 da ≥ 8 positivos entre las malas y ≤ 2 positivos entre las
  buenas; ajustar casos (no reglas) si no.

### T6 · README, guion de demo, CONTEXTO final — carril `opencode-worker` (deepseek-v4-pro)
Por qué: escritura sobre un sistema ya construido. Depende de T3b y T4.

- [x] `README.md` con la estructura obligatoria del §9 del prompt maestro, en ese orden: (1)
  pregunta del reto literal, (2) respuesta en tres frases, (3) enlace a la demo (marcador
  `<URL-DEMO>` que Fable reemplaza), (4) cómo probarlo en 60 segundos con un caso listo para
  pegar, (5) qué es real y qué es simulado, (6) enlace a `CONTRATO-DE-DATOS.md` y sección
  **Ruta de adopción** (qué área lo usa, con qué se conecta, desde cuándo, qué debe existir del
  lado de WIN en cada etapa), (7) quiénes somos con el reparto Motor/Superficie/Circuito y
  marcadores `<INTEGRANTE_1..3>`. Más: cómo correrlo local (`python -m venv`, `uvicorn`), cómo
  desplegar (Render/Fly/Docker), variables (`ANTHROPIC_API_KEY` opcional).
- [x] `docs/GUION-DEMO.md`: 5 minutos cronometrados por bloques de 30–60 s, qué se muestra en
  pantalla en cada uno, el lote del jurado, la confirmación desde un segundo teléfono, la
  bandeja, y la ruta de respaldo si no hay red (servidor local + `data/cases.json`).
- [x] `docs/CONTEXTO.md` actualizado: secciones 5 y 6 con el estado real (terminado / a
  medias / no empezado) leyendo el código.

### T7 · Verificación final contra los nueve bloqueantes — carril agente `sonnet` (curl, sin editar)
Por qué: el que construyó es el peor juez. Modelo distinto, ejecutando, no leyendo.

- [x] Levantar el servidor, recorrer los nueve bloqueantes del §6 del prompt maestro con
  `curl` (y `ANTHROPIC_API_KEY` sin definir para probar la degradación), reportar cada uno
  como PASA/FALLA con la evidencia (código HTTP, fragmento de HTML). No corregir nada.

## Criterios de aceptación

Los nueve bloqueantes del §6 del prompt maestro, verificados ejecutando. Además:
- Ninguna ruta devuelve 500 con entrada vacía, JSON inválido o CSV con columnas desconocidas.
- Cada regla disparada muestra `origen` en la UI.
- `SIMULADO` visible en todas las pantallas, incluida la del cliente.
- Con `ANTHROPIC_API_KEY` sin definir, la UI dice que la capa LLM no está disponible y todo
  funciona.

## Gates (en este orden)

```bash
.venv/bin/python -m compileall -q contracts engine app confirm
.venv/bin/pytest -q
.venv/bin/python -c "from app.main import app; print('app-ok')"
```

Workers: no commitear, no salir del alcance, no instalar dependencias fuera de
`requirements.txt` (si hace falta una, anotarla en el reporte y usar stdlib). Reporte final:
qué archivos tocaste, gates con salida, y qué quedó fuera.

---

## Adendum 2026-09-12 (tarde) — pedido del usuario: sin nombre, sin marca de agua, con IA real

### T8 · Rebrand: solo el logo de WIN, sin "Firme" ni "SIMULADO" — carril `opencode-worker` (deepseek-v4-pro)
Por qué: mecánico sobre ~25 archivos con juicio de redacción; hay patrón (los templates existentes).

- [ ] `app/templates/base.html`, `confirm/templates/client.html`, `confirm/templates/done.html`: quitar
  el `<span class="watermark">SIMULADO</span>` y el brand-mark "F"/"Firme". El header muestra el logo
  `/static/win-logo.png` (alto 40–44 px), el tagline "Que lo prometido sea lo entregado" y el badge de
  texto "Hackatón WIN Chiclayo 2026 · Reto 03". `app/static/app.css`: quitar `.watermark`; ajustar
  `.brand` para el logo. `<title>`: "… · WIN". Pie: una línea "Demostración con datos sintéticos;
  supuestos y fuentes visibles en cada evaluación." (sin la palabra SIMULADO).
- [ ] `app/main.py`: `FastAPI(title="WIN · Calidad de venta")`. `render.yaml` name y `fly.toml` app:
  `win-reto03`. `README.md`: título "# Que lo prometido sea lo entregado — WIN · Reto 03"; toda mención
  a "Firme" pasa a "la propuesta" / "el sistema". Mismo criterio en `docs/*.md`, `CONTRATO-DE-DATOS.md`
  y en las cadenas `fuente:` de `config/*.yaml` ("Plan del equipo (T1)…"). Encabezado de docs:
  "WIN · Hackatón Chiclayo 2026 · Reto 03". No tocar `contracts/`, `engine/`, `tests/`, `data/`.
- [ ] Verificar: `rtk proxy grep -rn 'Firme\|SIMULADO' --exclude-dir=.venv --exclude-dir=.git .` devuelve solo
  este plan; gates verdes.

### T9 · Capa de IA real con OpenCode Go — carril `codex-worker` (gpt-6-astra, xhigh)
Por qué: integración sin patrón, con degradación y latencia que cuidar.

**Proveedor:** OpenAI-compatible en `https://opencode.ai/zen/go/v1/chat/completions`. Cabeceras:
`Authorization: Bearer <key>`, `x-opencode-session: <uuid estable por proceso>` (sin ella responde
`MissingSessionID`). Clave: env `OPENCODE_API_KEY`; si no está, leer `~/.local/share/opencode/auth.json`
→ `["opencode-go"]["key"]` (comodidad local; nunca commitear la clave). Modelo por defecto
`deepseek-v4-flash` (env `LLM_MODEL`); `response_format: {"type": "json_object"}` funciona;
`temperature: 0`; latencia observada 9–11 s por llamada (razona internamente), por eso **una llamada por
lote, nunca una por fila**. Timeout 25 s. Cliente con `httpx` (ya instalado). Mantener el camino
Anthropic solo si `ANTHROPIC_API_KEY` está definido; prioridad: Anthropic → OpenCode → determinista.
`llm_mode` sigue siendo `"llm" | "determinista"`; agregar en `Verdict`… no: el contrato está congelado;
exponer el nombre del proveedor/modelo por `GET /salud` y en la UI con un texto "IA: DeepSeek (OpenCode
Go)" leído desde `engine.llm.describe()`.

Dónde aplica la IA (todas con salida verificable y degradación determinista):
1. **Promesa → estructura + claims semánticos** (`normalize_promises(texts: list[str], catalog) ->
   list[Promise]`, una llamada por lote; `normalize_promise` delega a ella con lista de uno). El prompt
   pide, además de plan/velocidad/precio/promo/plazo, `claims`: toda promesa que el catálogo no respalda
   (velocidad garantizada, sin contrato, precio congelado, instalación hoy/mañana sin falta, gratis para
   siempre, equipos extra). `facts.unsupported_claims` debe incluir los claims del LLM que no estén en
   el lexicon marcándolos como `origen: IA`; R23 sigue disparando. Los claims del lexicon se mantienen
   como red determinista.
2. **Mapeo semántico de columnas** (`map_columns(unrecognized: list[str], sample_row: dict) ->
   dict[str, str]`): solo cuando `IngestReport.unrecognized` no está vacío; una llamada por lote; el LLM
   propone campo de `Sale` para cada columna desconocida ("Nro. Cel. Titular" → `phone`); la ingesta
   aplica el mapeo y lo reporta como "mapeado por IA" en la vista de lote.
3. **Explicación del veredicto** (`explain_verdict(sale, verdict) -> str`): 2–3 frases en español que
   citan solo la evidencia disparada (regla, valores) y la decisión; prohibido inventar hechos. Se genera
   al ver `GET /ventas/{id}` la primera vez y se guarda en `state["explanations"][sale_id]` (recalcular
   si cambia el veredicto: comparar `expected_cost` y `decision`). La UI la muestra arriba de la cadena
   de evidencia como "Por qué, en palabras" con la etiqueta del proveedor.
4. **Resumen del lote** (`summarize_batch(rows) -> str`): una llamada tras `POST /lote`, con la tabla
   compacta (id, decisión, costo, reglas): patrones transversales (mismo vendedor, teléfonos
   compartidos, direcciones repetidas), qué revisar primero y por qué. Se muestra arriba de la tabla.
5. **Texto al cliente** (`explain_for_client`, ya existe): usar el mismo proveedor.

- [ ] `engine/llm.py`: cliente único (`_chat(messages, json=True) -> dict|None`), sesión uuid por
  proceso, prioridad de proveedores, `describe()`; nunca lanza; log a stderr en fallo.
- [ ] `engine/facts.py`: incorporar claims IA a `unsupported_claims` sin romper tests.
- [ ] `engine/ingest.py` + `app/main.py`: mapeo semántico opcional y reporte "por IA"; una llamada de
  normalización por lote (pasar `promise` ya normalizada a `evaluate_and_store` para que no vuelva a
  llamar); resumen del lote; explicación en veredicto; `GET /salud` con proveedor y modelo.
- [ ] Templates: bloques "Por qué, en palabras" (verdict.html) y "Lectura del lote" (batch.html), con la
  etiqueta del proveedor; si no hay IA, el bloque dice "IA no disponible: comparador determinista".
- [ ] Tests (`tests/test_llm.py`, con `monkeypatch` del cliente HTTP, sin red): prioridad de proveedores,
  degradación ante timeout/JSON inválido, claims IA llegan a R23, mapeo semántico aplicado.
- [ ] Verificación con computer-use al final (viewport móvil): formulario con promesa "Fibra 850 a
  S/ 59.50, velocidad garantizada y el precio nunca sube" → R23 con claim "el precio nunca sube" marcado
  IA; lote pegado con columnas raras ("Nro. Cel. Titular", "Tarifa mensual") → mapeadas por IA; resumen
  del lote visible; veredicto con "Por qué, en palabras"; `/salud` con el modelo. Y sin clave
  (`OPENCODE_API_KEY=` vacío y auth.json inaccesible por env `LLM_DISABLE=1`) todo sigue funcionando
  y lo dice en pantalla.

---

## Adendum 2 (2026-09-12, noche) — cumplir los entregables no-código del equipo

Fuente: los documentos del compañero, ya copiados al repo: `docs/RETO-03-FUENTE.md`,
`docs/EVIDENCIA-PUBLICA.md`, `docs/MODELO-DE-COSTO.md`, `docs/CASOS-ADVERSARIOS.md` y
`CONTRATO-DE-DATOS.md` (raíz; la versión anterior del prototipo quedó en
`docs/CONTRATO-DE-DATOS-prototipo-v1.md`). Esos documentos son el insumo del prototipo: **el
prototipo se adapta a ellos, no al revés.** Nombres de campo, estados de `confirmacion_titular`,
parámetros `P-NN`, vocabulario `pasa · revisar · abstención` y los 24 casos se cumplen tal cual.

### T10 · Cumplimiento del banco adversario, el contrato y el modelo de costo — carril `codex-worker` (gpt-6-astra, xhigh)
Por qué: toca motor, config, ingesta, datos y tests con criterios de aceptación exactos (24 veredictos).

**Contrato `contracts/types.py` sigue congelado.** Todo campo nuevo del Anexo 1 viaja en `Sale.extra`
con clave canónica (la del contrato) y el motor lo lee desde ahí (`engine/facts.py`).

1. **Ingesta (`engine/ingest.py`)** — sinónimos para los 30 campos del `CONTRATO-DE-DATOS.md` §4:
   `promesa_declarada→promise_text`, `velocidad_contratada→extra.velocidad_contratada` (si falta `plan`,
   derivar el id de plan por velocidad en cualquier superficie del catálogo; si ninguna la tiene, `plan`
   = "<N> Mbps" para que dispare R04), `precio_mensual→price`, `cliente_documento→customer_doc`,
   `telefono_1→phone`, `telefono_2→extra`, `correo_electronico→email`, `direccion→address`,
   `nombre_asesor→seller_id`, `equipo→extra.equipo`, `canal→channel`, `fecha_hora_registro→registered_at`,
   `ediciones_registro→edits`, `plazo_estimado_instalacion→extra`, `confirmacion_titular(+_ts)→extra`,
   y a `extra` con clave canónica: `plazo_vigencia`, `forma_entrega_recibo`, `forma_pago`,
   `forma_pago_instalacion`, `cargo_instalacion_costo`, `cargo_instalacion_cuotas`, `tenencia`, `etapa`,
   `nombre_condominio`, `torre`, `departamento`, `score_crediticio`, `catalogo_referencia_id`,
   `acta_instalacion_ts`. Etiquetas: además de buena/mala aceptar `pasa→buena`, `revisar→mala`,
   `abstención|abstencion→label None + extra.veredicto_esperado="abstención"`; cualquier columna
   `veredicto_esperado` se conserva en `extra`.
2. **Estados de consentimiento** (`CONTRATO-DE-DATOS.md` §6) → `facts.confirmation_status`: si hay
   `Context.confirmation` manda ella; si no, `extra.confirmacion_titular`: `confirmada→confirmada`,
   `negada→desconocida`, `enviada→pendiente`, `no_respondida→silencio`,
   `confirmada_con_correccion→corregida`, `no_enviada→None`. `facts.confirmation_ts` desde
   `extra.confirmacion_titular_ts` o `Confirmation.responded_at`. La UI muestra ambos vocabularios
   ("Confirmada · `confirmada`", "Sin respuesta · `no_respondida`", …). El flujo `/c/{token}` sigue igual.
3. **Catálogo (`config/catalog.yaml`)** según `docs/EVIDENCIA-PUBLICA.md` §1, §2 y §4:
   - `surfaces`: `cartilla` (documento legal, `origen: PUBLICO`, fuente
     `https://win.pe/files/cartilla-informativa.pdf?ver=1.2`, `governs_contract: true`), `web_hogar`
     (`https://win.pe/hogar`, promo 1 mes), `web_chiclayo` (`https://win.pe/chiclayo`, promo 3 meses),
     ambos `origen: PUBLICO`, fecha 2026-09-12, nota "verificar en vivo antes de presentar".
   - Planes canónicos = cartilla: `fibra_100` 79.00 (`zones: [provincias]`), `fibra_200` 99.00,
     `fibra_300` 119.00, `fibra_400` 129.00, `fibra_600` 169.00, `fibra_1000` 259.00, todos
     `surfaces: [cartilla]` (1000 también en las web). Escalones solo web: `fibra_350`, `fibra_550`,
     `fibra_750` (web_chiclayo), `fibra_500`, `fibra_850` (web_hogar), con `surfaces` y los precios
     observados el 2026-09-12 cuando se conocen (500: 99.00; 750: 54.50; 850: 59.50; 1000 web: 69.50,
     etiquetados "tarifa introductoria, verificar") o `price: null`.
   - `promo_prices`: `fibra_100: 39.50` (`origen: SUPUESTO_DEMO`, ejemplo de EVIDENCIA-PUBLICA §3.1).
   - `installation: {cost: 120.00, quotas: 6, quota: 20.00, id: P-02, origen: PUBLICO}`,
     `paper_invoice_fee: {amount: 10.00, id: P-03}`, `forced_term_months: {value: 6, id: P-04}`,
     `min_credit_score: {value: 201, origen: PUBLICO, fuente: "cartilla §2.3"}`, `mesh: {included: false,
     note: "a solicitud", origen: PUBLICO}`.
   - `coverage`: mantener distritos SUPUESTO_DEMO para la demo y agregar `regions`: `lima` (Lima
     Metropolitana, Callao, Barranca, Huaral, Hualmay, Huacho) y `provincias` (Santa, Trujillo, Chiclayo,
     Lambayeque, Piura). `facts.address_region` se deriva del texto de `address`/`district` ("lima" si
     contiene "lima" y no "lambayeque"; "provincias" si contiene una ciudad de provincias; si no, None).
4. **Costos (`config/costs.yaml`)** con el registro `P-NN` de `docs/MODELO-DE-COSTO.md` §3, cada
   parámetro con `id`, `origen` y `fuente`: costos unitarios `instalacion_fallida: 80.00 (P-09)`,
   `baja_temprana: 95.00 (P-11)`, `reclamo: 45.00 (P-13)`, `reversion_facturacion: 58.00 (P-15)`;
   probabilidades base de una venta señalada `P-08 0.05, P-10 0.06, P-12 0.10, P-14 0.15`
   (documentadas; cada regla declara su impacto propio, nunca menor que la base para severidad ≥ media);
   `review: {minutes: 12 (P-16), cost_per_minute: 2.50 (P-17), cost: 30.00}`; `recoverability: 1.0`
   (§6: una revisión a tiempo evita el desenlace); `thresholds.retain_multiple: 4` (RETENER = 4 × revisar
   o evidencia bloqueante; es un refinamiento del prototipo dentro de la familia `revisar`); priors
   `SUPUESTO_DEMO` por canal más `priors_by_seller` (`ASESOR-014: 0.10`) y `priors_by_team`
   (`EQUIPO-CHICLAYO-02: 0.08`); `prior = max(canal, asesor, equipo)`; el prior solo nunca supera el
   costo de revisar. La UI dice "Costo de revisar = P-16 × P-17 = S/ 30,00" y "Costo esperado ≥ costo de
   revisar → revisar".
5. **Ventanas (`config/settings.yaml`)**: `install_ceiling_days: 30 (P-01)`, `install_median_days: 10
   (P-07)`, `verification_window_days: 10` (= P-07), `confirmation_window_hours: 240` (derivada),
   `alert_buffer_hours: 24`; quitar `install_window_hours` y usar `install_ceiling_days` en R11 y avisos.
6. **Reglas nuevas (`config/rules.yaml`)**, todas con `source`/`fuente` citando el documento y sección:
   - `R30_permanencia_prometida` (promesa-registro, alta, PUBLICO cartilla §2.5): claims contiene "sin
     permanencia" (léxico: sin permanencia, sin contrato, se puede ir cuando quiera, sin plazo forzoso) y
     `plazo_vigencia` empieza con "forzoso".
   - `R31_recibo_fisico_no_declarado` (promesa-registro, media, PUBLICO Anexo 1): `forma_entrega_recibo`
     = físico, `promise_price` no nulo y la promesa no menciona "recibo" (`facts.promise_mentions_recibo`).
     BUE-02 no dispara; DEF-04 sí.
   - `R32_score_bajo_minimo` (catalogo-registro, alta, PUBLICO cartilla §2.3): `score_crediticio < 201`.
   - `R33_titular_no_verificable` (identidad, `abstain: true`, PUBLICO Anexo 1): `tenencia` = inquilino,
     confirmación `confirmada`, `phone` presente y `consent_evidence` vacío → ABSTENERSE con motivo "la
     confirmación llegó al teléfono registrado y no hay evidencia de que ese número sea del firmante".
     BUE-03 (sin teléfono) no dispara; AMB-04 sí.
   - `R34_condominio_sin_unidad` (registro-entrega, media, PUBLICO Anexo 1): `nombre_condominio` presente y
     falta `torre` o `departamento`.
   - `R35_primera_factura_no_declarada` (registro-entrega, media, PUBLICO cartilla §2.2/§2.6):
     `cargo_instalacion_cuotas` o `cargo_instalacion_costo` presentes, `promise_price` no nulo y la
     promesa no menciona cuota/instalación (`facts.promise_mentions_installation_fee`). Mensaje con la
     composición de la primera factura (prorrateo + renta + cuota S/ 20 + S/ 10 si recibo físico).
     BUE-01 no dispara; LIM-01 sí.
   - `R36_plan_fuera_de_zona` (registro-entrega, alta, PUBLICO cartilla §2.1): el plan tiene `zones:
     [provincias]` y `address_region == "lima"`. BUE-04 no; LIM-05 sí.
   - `R37_catalogo_ambiguo` (promesa-catalogo, `abstain: true`, CONTRADICCIÓN EVIDENCIA §1/§8): la
     velocidad registrada o prometida existe solo en superficies web y `catalogo_referencia_id` es nulo.
     AMB-03 sí. Nuestros 25 casos de demo migran a escalones de la cartilla para no abstenerse.
   - `R38_promo_duracion_no_verificable` (promesa-catalogo, `abstain: true`, CONTRADICCIÓN): la promesa
     menciona duración promocional (regex `promocional|por \d+ meses|despu[eé]s sube|luego sube`) y
     `catalogo_referencia_id` es nulo. AMB-05 sí.
   - `R39_confirmacion_tardia` (identidad, media, SUPUESTO P-07): confirmación `confirmada` con
     `confirmation_ts` posterior a `registered_at + verification_window_days`. LIM-04 sí (ver dato 8).
   - Ajustes: colisión de teléfono/correo/documento = mismo contacto y **algún** atributo de identidad
     conocido en ambos y distinto (`customer_name`, `customer_doc` o `address`), ya no exige nombres;
     R17 dirección repetida agrega `and not (torre and departamento)`; `decide()`: evidencia con
     `abstain: true` → ABSTENERSE con `abstain_reason` = mensaje, salvo que haya bloqueante.
   - Léxico: sumar "routers mesh incluidos", "mesh incluido", "equipos incluidos sin costo" (inexistente,
     PUBLICO EVIDENCIA §1 "a solicitud"), "sin permanencia" y alias, "todo incluido" (insostenible si hay
     recargos no declarados; que R31/R35 lo usen como refuerzo, no como regla propia).
7. **Vocabulario en la UI**: cada decisión muestra su equivalente del modelo de costo: `APROBAR · pasa`,
   `REVISAR · revisar`, `RETENER · revisar (prioridad máxima)`, `ABSTENERSE · abstención`. Matriz de
   confusión: positivo = familia revisar; fila adicional "abstenciones esperadas acertadas" cuando
   `extra.veredicto_esperado` = abstención.
8. **Datos**: `data/casos-adversarios.json` con los 24 casos **exactamente** con las claves y valores de
   `docs/CASOS-ADVERSARIOS.md` (`id`: BUE-01…LIM-05, más `veredicto_esperado`, `familia`, `comparador`
   y `extra.simulado: true`). Única adición documentada: LIM-04 necesita un ancla temporal que el banco
   omite; agregar `fecha_hora_registro: "2026-08-30T10:00:00-05:00"` y anotarlo en `nota_demo`. Los 25
   casos de `data/cases.json` migran a los escalones de la cartilla (200/300/400/600/1000, precios de la
   cartilla) conservando la intención de cada uno. Botón "Cargar los 24 casos adversarios" en `/lote`.
9. **Tests**: `tests/test_adversarial.py` recorre los 24 casos por `engine.ingest.parse` + `evaluate`
   con historial = el lote completo y exige: `pasa → APROBAR`, `revisar → REVISAR o RETENER`,
   `abstención → ABSTENERSE`, y que la regla principal coincida con el comparador del caso (tabla en el
   test). `tests/test_app.py` sigue exigiendo 13/13 y 0 falsos positivos en los 25 de demo. Ajustar
   impactos de reglas (no umbrales ni costos P-NN) hasta que ambos bancos pasen.
10. **Verificación con computer-use** (viewport móvil): `/lote` → "Cargar los 24 casos adversarios" →
    matriz y lista con los veredictos esperados vs obtenidos; abrir DEF-04, LIM-01, AMB-03 y LIM-05 y
    confirmar la regla, la fuente `PUBLICO` con sección y el vocabulario `pasa/revisar/abstención`;
    pegar el JSON de BUE-02 y DEF-04 juntos y ver que solo DEF-04 dispara R31.

### T10b · Integrar los documentos del equipo en README, GUION y CONTEXTO — carril `opencode-worker` (deepseek-v4-pro)
Depende de T10. README: pregunta y respuesta se mantienen; "Cómo probarlo en 60 s" usa los nombres del
Anexo 1 (`promesa_declarada`, `velocidad_contratada`, `precio_mensual`, `forma_entrega_recibo`,
`confirmacion_titular`); nueva sección "Los tres catálogos de WIN" (EVIDENCIA §1, como hallazgo de
arquitectura de información); tabla de documentos con los cinco entregables del equipo; vocabulario
`pasa/revisar/abstención`; costo de revisar `P-16 × P-17`. `CONTRATO-DE-DATOS.md`: apéndice
"Correspondencia con el prototipo" (campo del contrato → campo `Sale` o clave `extra`, y qué regla lo
usa). GUION: bloque del banco adversario. CONTEXTO: estado real.
