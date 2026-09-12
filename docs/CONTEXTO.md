# Contexto del proyecto

WIN · Hackatón Chiclayo 2026 · Reto 03

Este documento es el artefacto de traspaso: lo primero que se le da a cualquier
persona o modelo que entra a mitad de camino. Se actualiza al cerrar cada fase.

**Estado del proyecto: construido y commiteado de punta a punta. Pendiente: el
despliegue a una URL pública.**

---

## 1. Qué es esto y qué pregunta responde

La propuesta responde a la pregunta del reto: ¿cómo verificamos que cada venta fue
hecha como debe ser —con el cliente correcto y con la promesa correcta— antes de
que se convierta en instalación, factura y problema?

Un jurado pega un lote de ventas que nunca vimos, y el sistema separa las buenas
de las malas explicando **qué no coincide con qué** (promesa ↔ catálogo ↔
registro ↔ entregable), con costo esperado en soles, contrafáctico y
confirmación del cliente por enlace.

La unidad de análisis no es la venta registrada sino **la promesa**: el defecto
vive en la distancia entre lo que se le dijo al cliente y lo que el sistema va a
entregar.

---

## 2. Stack y estructura de carpetas

- Python 3.13, FastAPI + Jinja2 + CSS/JS vanilla (móvil primero), PyYAML,
  pydantic, pytest. Un solo proceso `uvicorn app.main:app`.
- Estado en `data/state.json` (`app/store.py`). Sin build step, sin frameworks
  JS, sin base de datos.
- Intérprete siempre `.venv/bin/python` / `.venv/bin/pytest`.

```
contracts/       tipos compartidos congelados (Sale, Verdict, Promise, ...)
engine/          motor: facts, rules, cost, counterfactual, llm, ingest
app/             FastAPI: rutas, templates, static
confirm/         confirmación del cliente y enlace por token
config/          reglas, catálogo, costos, léxico y ventanas en YAML
data/            casos sintéticos (cases.json, casos-adversarios.json)
tests/           motor, ingesta, IA, app y banco adversario
docs/            CONTEXTO, preguntas, entrevista, guion
```

---

## 3. Decisiones cerradas

No se reabren. Cada una con su porqué.

- **Stack único** (FastAPI + Jinja2 + vanilla, un proceso, JSON como estado):
  minimiza la infraestructura y el tiempo hasta una demo que corre; nada que
  aprovisionar.
- **Idioma dividido:** UI en español neutro profesional; código, identificadores,
  archivos y comentarios en inglés. El jurado es hispanohablante y el código es
  para el equipo.
- **Solo datos sintéticos:** cero datos reales de personas; todo caso es
  sintético.
- **Reglas, catálogo, costos y umbrales en `config/*.yaml`**, cada ítem con
  `origen: SUPUESTO_DEMO | PUBLICO` y `fuente`: nunca inventar política
  comercial de WIN; la UI muestra el origen junto a cada regla disparada.
- **Condiciones de reglas con `eval`** sobre un dict plano de `facts` y
  `__builtins__` vacío: las reglas son config confiable, los datos solo valores.
- **Contrato congelado en `contracts/types.py`:** nadie lo edita sin avisar a
  los otros; los entrypoints públicos del motor son `engine.evaluate`,
  `engine.ingest.parse` y `engine.llm.normalize_promise`.
- **Capa de IA** (proveedor **OpenCode Go**, endpoint compatible con OpenAI en
  `https://opencode.ai/zen/go/v1`, modelo por defecto `deepseek-v4-flash`;
  alternativa `ANTHROPIC_API_KEY` con `claude-opus-5`): prioridad Anthropic →
  OpenCode Go → comparador determinista. Sin clave (`OPENCODE_API_KEY` /
  `ANTHROPIC_API_KEY`), sin red, con `LLM_DISABLE=1` o ante excepción, degrada a
  comparador determinista y lo dice en pantalla (`llm_mode`). La IA extrae, mapea
  y explica; **nunca decide**. La demo nunca depende de una llamada externa.
- **Ventana de diseño** (`install_ceiling_days: 30` = P-01, techo contractual del
  Anexo 1; `install_median_days` y `verification_window_days: 10` = P-07;
  `confirmation_window_hours: 240`; `alert_buffer_hours: 24`): toda la
  arquitectura se justifica contra el tiempo entre venta e instalación, no contra
  la exactitud teórica.
- **Decisión por costo esperado**, no por score: `p(outcome) = 1 − Π(1 − p_i)`
  (noisy-OR) más prior por canal; `expected_cost = Σ p(o) × cost(o)`; el corte
  es donde el costo esperado supera el costo de revisar. La cola se ordena por
  `recoverable_per_minute`.
- **Sin auth** salvo el token del enlace de confirmación
  (`secrets.token_urlsafe(8)`).
- **Fuera de alcance:** auth, multiusuario, roles, telemetría, migraciones,
  paginación, modo oscuro, envío real de correo/WhatsApp, versionado de config,
  tests fuera del motor.

---

## 4. Dónde vive el estado

| Qué | Archivo |
|---|---|
| Reglas del rombo y señales | `config/rules.yaml` |
| Planes, promos, cobertura, alias | `config/catalog.yaml` |
| Desenlaces, costos, umbrales, priors | `config/costs.yaml` |
| Frases de promesa insostenibles, alias | `config/lexicon.yaml` |
| Ventanas y parámetros de señales | `config/settings.yaml` |
| Casos sintéticos etiquetados | `data/cases.json` |
| Banco de 24 casos adversarios | `data/casos-adversarios.json` |
| Tipos compartidos | `contracts/types.py` |
| Estado en ejecución | `data/state.json` |

En `data/state.json`, además de `sales`, `verdicts`, `events` y `confirmations`,
vive `state['explanations']`: el caché de las explicaciones "Por qué, en
palabras" por venta, invalidado por la firma de la evidencia (decisión, costo
esperado y cadena de evidencia).

---

## 5. Cómo levantarlo y recorrerlo de punta a punta

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Abrir `http://127.0.0.1:8000`. Una pantalla por función:

- `GET /` — formulario de venta (móvil primero, botón "Cargar ejemplo").
- `POST /ventas` → `GET /ventas/{id}` — veredicto: decisión, costo esperado,
  cadena de evidencia, contrafáctico y bloque de confirmación.
- `GET/POST /ventas/{id}/editar` — edición que alimenta la señal de reedición.
- `GET /lote` · `POST /lote` — pegar o subir JSON/CSV, o "Cargar los 25 casos de
  demo"; reporte de ingesta, tabla y matriz de confusión.
- `POST /confirm/create/{id}` → `GET /c/{token}` · `POST /c/{token}` —
  confirmación del cliente por enlace; `POST /confirm/expire/{id}` simula el
  silencio.
- `GET /bandeja` · `POST /bandeja/{id}/hecho` — avisos con destinatario,
  urgencia y plazo.
- `GET /salud` — `{"ok": true, "llm": "..."}`.

Gates, en este orden:

```bash
.venv/bin/python -m compileall -q contracts engine app confirm
.venv/bin/pytest -q
.venv/bin/python -c "from app.main import app; print('app-ok')"
```

---

## 6. Qué está terminado, qué está a medias, qué no se empezó

**Estado real, leído del código (12/09). T1–T10 terminados y commiteados; T10b
(documentación) en curso. Falta solo el despliegue a una URL pública, pendiente
de crear la cuenta de hosting.**

- **Terminado:**
  - `contracts/types.py` (congelado) y `app/store.py` (JSON + lock de proceso).
  - Motor (`engine/`): `evaluate`, facts, 39 reglas en `config/rules.yaml`
    (R01–R29 del rombo y las señales, R30–R39 del banco adversario), costo
    esperado (noisy-OR sobre los parámetros `P-NN` de `MODELO-DE-COSTO.md`),
    decisión, contrafáctico, capa de IA (OpenCode Go) con degradación
    determinista e ingesta tolerante (`engine.ingest.parse`, sinónimos de los 30
    campos del contrato).
  - Config (`config/*.yaml`): catálogo de la **cartilla** con **tres
    superficies** (`cartilla`, `web_hogar`, `web_chiclayo`), reglas, costos
    (costo de revisar = P-16 × P-17 = S/ 30,00), léxico y ventanas.
  - Web (`app/`): formulario, veredicto, edición, lote, bandeja y salud. El
    veredicto muestra el vocabulario del modelo de costo: `pasa` / `revisar` /
    `revisar (prioridad máxima)` / `abstención`.
  - Confirmación (`confirm/`): enlace por token, pantalla del cliente,
    corregir/desconocer y silencio.
  - `data/cases.json`: 25 casos sintéticos de demo. `data/casos-adversarios.json`:
    los 24 casos del banco, clasificados **24/24** según el veredicto esperado y
    la regla principal de cada caso.
  - Despliegue listo: `Dockerfile`, `render.yaml`, `fly.toml`.
  - Tests: 97 verdes (`tests/test_engine.py`, `test_ingest.py`, `test_llm.py`,
    `test_app.py`, `test_adversarial.py`).
- **A medias:** —
- **No empezado / pendiente:** despliegue a URL pública (falta la cuenta de
  hosting); edición de
  umbrales desde la UI (solo si sobra tiempo).

Fases: T1 motor ✓ · T2 documentos + contrato ✓ · T3 web ✓ · T3b ingesta/lote ✓ ·
T4 confirmación ✓ · T5 casos ✓ · T6 README/guion/contexto ✓ · T7 verificación ✓
(nueve bloqueantes PASA) · T8 rebrand ✓ · T9 IA real ✓ · T10 cumplimiento del
banco, contrato y modelo de costo ✓ · T10b documentación (este cierre).

---

## 7. Supuestos sin confirmar + aprendizajes del mentor

### Supuestos sin confirmar

Todo lo marcado `SUPUESTO_DEMO` en `config/` está pendiente de verificar con el
mentor o contra fuentes públicas (`win.pe`):

- El catálogo completo de planes, promos, precios y condiciones de combinación.
- La cobertura por distrito y la velocidad máxima por zona.
- Los costos de los desenlaces (instalación fallida, reclamo, baja temprana,
  reversión de facturación), la tasa de recuperación y el costo de una revisión.
- Los priors de defecto por canal y la ventana real venta→instalación.

Ninguno de estos valores se presenta como dato real de WIN.

### Aprendizajes del mentor

_Vacío — se llena después de la conversación con el mentor._

Plantilla por aprendizaje:

```
- [ ] Pregunta hecha:
      Respuesta:
      Qué cambiamos en el diseño:
```

### Dudas de diseño

_Vacío — se llena cuando una decisión quede abierta o en conflicto._

Plantilla por duda:

```
- [ ] Duda:
      Contexto:
      Opciones barajadas:
      Qué bloquea resolverla:
```
