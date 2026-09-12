# Contexto del proyecto

Prometido · Hackatón WIN Chiclayo 2026 · Reto 03

Este documento es el artefacto de traspaso: lo primero que se le da a cualquier
persona o modelo que entra a mitad de camino. Se actualiza al cerrar cada fase.

**Estado del proyecto: en construcción.**

---

## 1. Qué es esto y qué pregunta responde

Prometido responde a la pregunta del reto: ¿cómo verificamos que cada venta fue
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
data/            casos sintéticos etiquetados (cases.json)
tests/           solo el motor (test_engine.py)
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
- **Marca `SIMULADO` en todas las pantallas:** cero datos reales de personas;
  todo caso es sintético.
- **Reglas, catálogo, costos y umbrales en `config/*.yaml`**, cada ítem con
  `origen: SUPUESTO_DEMO | PUBLICO` y `fuente`: nunca inventar política
  comercial de WIN; la UI muestra el origen junto a cada regla disparada.
- **Condiciones de reglas con `eval`** sobre un dict plano de `facts` y
  `__builtins__` vacío: las reglas son config confiable, los datos solo valores.
- **Contrato congelado en `contracts/types.py`:** nadie lo edita sin avisar a
  los otros; los entrypoints públicos del motor son `engine.evaluate`,
  `engine.ingest.parse` y `engine.llm.normalize_promise`.
- **LLM opcional** (SDK `anthropic`, `claude-opus-5`, `output_format=...`,
  timeout 10 s): sin clave, sin red o ante excepción, degrada a comparador
  determinista y lo dice en pantalla (`llm_mode`). La demo nunca depende de una
  llamada externa.
- **Ventana de diseño** (`install_window_hours: 48`, `confirmation_window_hours:
  24`, `alert_buffer_hours: 12`): toda la arquitectura se justifica contra el
  tiempo entre venta e instalación, no contra la exactitud teórica.
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
| Tipos compartidos | `contracts/types.py` |
| Estado en ejecución | `data/state.json` |

---

## 5. Cómo levantarlo y llegar al primer veredicto

```bash
.venv/bin/uvicorn app.main:app --port 8765
```

Abrir `http://localhost:8765`, cargar una venta por el formulario (o "Cargar
ejemplo") y `POST /ventas` redirige a `GET /ventas/{id}`, que muestra decisión,
costo esperado, cadena de evidencia y contrafáctico.

Gates, en este orden:

```bash
.venv/bin/python -m compileall -q contracts engine app confirm
.venv/bin/pytest -q
.venv/bin/python -c "from app.main import app; print('app-ok')"
```

---

## 6. Qué está terminado, qué está a medias, qué no se empezó

**En construcción — pendiente de actualizar al cerrar cada fase.**

- Terminado: `contracts/types.py` (congelado), `app/store.py`, esqueleto del repo.
- A medias: —
- No empezado: motor (`engine/`), config (`config/*.yaml`), aplicación web
  (`app/`), confirmación (`confirm/`), casos (`data/cases.json`), despliegue.

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
