# Guion de demo — WIN (5 minutos)

Objetivo: que el jurado abra el prototipo en su teléfono, le dé un lote que nunca
vimos, y vea cómo el sistema lo separa y lo explica. Cinco minutos cronometrados,
en bloques de 30–60 segundos. Al final, la ruta de respaldo sin red.

Datos sintéticos en todas las pantallas: se menciona una vez al inicio y no se
vuelve a justificar.

---

## Bloque 1 · La pregunta y la tesis — 0:00–0:40 (40 s)

**En pantalla:** `GET /` (formulario "Nueva venta", móvil primero). Se señala el
logo de WIN y el pie con el encuadre.

**Qué se dice:**

- La pregunta del reto, en una línea: *¿cómo verificamos que cada venta fue hecha
  como debe ser, con el cliente correcto y con la promesa correcta, antes de que
  se vuelva instalación, factura y problema?*
- La tesis: la unidad de análisis no es la venta registrada, es **la promesa**.
  Comparamos cuatro representaciones de la misma venta y cada desacuerdo es un
  defecto explicable.

---

## Bloque 2 · Una venta entra y sale un veredicto — 0:40–1:30 (50 s)

**En pantalla:** formulario → "Cargar ejemplo" o completar a mano una venta con
un defecto (p. ej. promesa con "velocidad garantizada"). Enviar → `GET
/ventas/{id}`.

**Qué se muestra y se dice:**

- Decisión grande y **costo esperado en soles**, descompuesto en probabilidad ×
  costo de cada desenlace.
- La **cadena de evidencia**: qué regla, qué condición, qué valores la dispararon,
  de qué fuente sale, con su etiqueta `origen` (SUPUESTO_DEMO / PÚBLICO).
- El **claim sin respaldo marcado `origen: IA`** en la cadena de evidencia, que
  alimenta la regla R23 (promesa insostenible).
- La explicación **"Por qué, en palabras"**: la IA redacta el porqué citando solo
  las reglas y los valores que se dispararon.
- El **contrafáctico**: "si el campo X fuera Y, esta venta pasaría".
- La línea que lo ancla: el corte no se elige a dedo; es donde el costo esperado
  supera el costo de revisar.

---

## Bloque 3 · El lote del jurado — 1:30–2:30 (60 s)

**En pantalla:** `GET /lote`. Pegar el lote del jurado (JSON o CSV con esquema
desconocido) o tocar "Cargar los 25 casos de demo".

**Qué se muestra y se dice:**

- El **reporte de ingesta**: columnas mapeadas, no reconocidas y faltantes, con
  las columnas ajenas que la IA mapea (`mapeado por IA`). La ingesta tolera
  esquemas ajenos y **no se cae** con filas corruptas.
- La **"Lectura del lote"**: resumen que redacta la IA con los patrones
  transversales y la prioridad de revisión.
- La tabla ordenada por **costo recuperable por minuto de revisión**, no por
  score.
- La **matriz de confusión** contra las etiquetas del lote (positivo = REVISAR o
  RETENER).

*Si el jurado trae su propio lote, este bloque absorbe el tiempo extra del
bloque 5.*

---

## Bloque 4 · La confirmación desde un segundo teléfono — 2:30–3:30 (60 s)

**En pantalla:** el veredicto → `POST /confirm/create/{id}` genera un enlace corto.
En un **segundo teléfono** (o en el del jurado) se abre `GET
/c/{token}`.

**Qué se muestra y se dice:**

- El cliente ve la promesa en **lenguaje llano**: "Hola {nombre}. {vendedor} te
  ofreció: {plan} a S/ {precio}/mes. ¿Es esto lo que acordaste?" con tres botones
  grandes.
- Tocar **"No pedí este servicio"** (o "Quiero corregir algo"). Al volver al
  veredicto, **la decisión cambió** (hacia RETENER) porque el cliente es el
  verificador de "quién está del otro lado".
- Una frase: el **silencio** (no responder antes de la ventana) se trata como la
  señal más fuerte del sistema.

---

## Bloque 5 · La bandeja y el plazo — 3:30–4:15 (45 s)

**En pantalla:** `GET /bandeja`.

**Qué se muestra y se dice:**

- Cada aviso con **destinatario, urgencia y plazo restante** y una acción concreta
  ("No despachar. Verificar con el cliente por el enlace").
- La cola se ordena por costo recuperable por minuto. Botón "Hecho" para cerrar
  el aviso.
- Si sobra tiempo, `POST /confirm/expire/{id}` simula la ventana vencida y muestra
  cómo el silencio dispara la retención.

---

## Bloque 6 · Qué pasa si WIN lo adopta, y cierre — 4:15–5:00 (45 s)

**En pantalla:** no se muestra pantalla nueva (o se vuelve al README/CONTRATO).

**Qué se dice:**

- La ruta de adopción en una línea por etapa: día uno autónomo → registro por API
  → promesa y reedición como datos → cierre del arco con webhooks de despacho,
  facturación y atención.
- El cierre con el encuadre: **protege las ventas buenas de quedar atrapadas en
  revisión, al cliente de una promesa que no se sostiene y al vendedor honesto de
  cargar con el costo del que no lo es.**

---

## Ruta de respaldo si no hay red

La demo **no depende de la red**: la capa de IA degrada a comparador determinista
y lo dice en pantalla.

- **Servidor local:** `.venv/bin/uvicorn app.main:app` y abrir
  `http://localhost:8000` (o exponer el portátil como punto de acceso).
- **Lote sin internet:** tocar "Cargar los 25 casos de demo" (`data/cases.json`):
  el lote etiquetado ya vive en el repo y no necesita conexión.
- **Confirmación en vivo:** abrir el enlace en el propio dispositivo o en un
  segundo teléfono conectado al punto de acceso del portátil.
- **Sin `ANTHROPIC_API_KEY`:** todo funciona; la pantalla indica "Capa LLM: no
  disponible, comparador determinista".
- **Sin clave de IA (`OPENCODE_API_KEY` / `ANTHROPIC_API_KEY`) o con
  `LLM_DISABLE=1`:** todo funciona igual; la pantalla indica "IA no disponible:
  comparador determinista".

Orden de repliegue si algo se cae: lote local → formulario manual → bandeja.
Nunca se detiene la demo para recuperar la red.
