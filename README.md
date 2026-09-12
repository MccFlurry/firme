# Que lo prometido sea lo entregado — WIN · Reto 03

Hackatón WIN Chiclayo 2026 · Reto 03 · Área dueña: Calidad de venta.

---

## 1. La pregunta del reto

> **RETO 03 · ÁREA DUEÑA: CALIDAD DE VENTA · VENTAS · EXPERIENCIA CLIENTE**
>
> **QUE LO PROMETIDO SEA LO ENTREGADO**
>
> **LA PREGUNTA:** ¿Cómo verificamos que cada venta que entra fue hecha como debe
> ser, con el cliente correcto y con la promesa correcta, antes de que se
> convierta en una instalación, una factura y un problema?

---

## 2. Nuestra respuesta, en tres frases

La propuesta trata la **promesa** como objeto de primera clase: en lugar de puntuar
la venta registrada, compara cuatro representaciones de la misma venta —lo que se
prometió, el catálogo vigente, lo que quedó registrado y lo que se va a entregar—
y cada desacuerdo entre dos de ellas es un defecto que se explica con nombres y
valores, no con un score opaco. Cada defecto se traduce a **costo esperado en
soles** (probabilidad × costo de instalación fallida, reclamo, baja temprana o
reversión de facturación) y la venta se revisa o retiene solo cuando ese costo
supera el costo de revisarla. El cliente cierra el círculo: un enlace de
confirmación de veinte segundos, antes de instalar, valida quién está del otro
lado, y su silencio se trata como la señal más fuerte del sistema.

El encuadre de todo el producto: **protege las ventas buenas de quedar atrapadas
en revisión, protege al cliente de una promesa que no se sostiene y protege al
vendedor honesto de cargar con el costo del que no lo es.** No es vigilancia
sobre el vendedor.

El veredicto habla en el vocabulario del modelo de costo: **APROBAR · pasa**,
**REVISAR · revisar**, **RETENER · revisar (prioridad máxima)** y
**ABSTENERSE · abstención**. El costo de revisar es `P-16 × P-17` = 12 minutos ×
S/ 2,50 = **S/ 30,00**; una venta se revisa o retiene solo cuando su costo
esperado supera el costo de revisarla.

---

## Los tres catálogos de WIN

La evidencia pública (`docs/EVIDENCIA-PUBLICA.md` §1) muestra que WIN publica
**tres catálogos comerciales distintos y mutuamente inconsistentes** en su propio
dominio:

| Fuente | Escalones de velocidad | Precios | Promoción |
|---|---|---|---|
| Cartilla informativa (documento legal, feb-2024) | 100 · 200 · 300 · 400 · 600 · 1000 Mbps | S/ 79 – S/ 259 | no menciona |
| `win.pe/hogar` | 500 · 850 · 1000 Mbps | S/ 99 – S/ 179,90 | 1 mes |
| `win.pe/chiclayo` | 350 · 550 · 750 · 1000 Mbps | S/ 79 – S/ 159,90 | 3 meses |

Validar una promesa exige un catálogo de referencia único, y WIN no lo tiene: un
vendedor puede prometer de buena fe algo de la página de Chiclayo mientras el
contrato que firma el cliente se rige por la cartilla. **Parte del problema que
el reto describe existe aguas arriba del vendedor.** Lo exponemos como hallazgo
de arquitectura de información, nunca como señalamiento.

---

## 3. Demo en vivo

**https://idealistic-carmela-preneolithic.ngrok-free.dev**

Sin credenciales y sin instalar nada: ábrela en tu propio teléfono.

> Túnel temporal (ngrok) al servidor del equipo: si el primer acceso muestra la
> página intermedia de ngrok, toca *Visit Site*. Para una URL permanente, el repo
> incluye `render.yaml`, `fly.toml` y `Dockerfile` (ver *Cómo desplegar*).

---

## 4. Cómo probarlo en 60 segundos

1. Abre la demo y ve a **Lote** (en la barra superior).
2. Pega este lote de dos filas, con los nombres exactos del **Anexo 1** del
   contrato (`promesa_declarada`, `velocidad_contratada`, `precio_mensual`,
   `forma_entrega_recibo`, `confirmacion_titular`):

   ```json
   [
     {"promesa_declarada": "Plan de 200 megas a 99 soles al mes", "velocidad_contratada": 200, "precio_mensual": 99.00, "forma_entrega_recibo": "Electronico", "confirmacion_titular": "confirmada", "etiqueta": "pasa"},
     {"promesa_declarada": "99 soles al mes, todo incluido", "velocidad_contratada": 200, "precio_mensual": 99.00, "forma_entrega_recibo": "Fisico", "confirmacion_titular": "confirmada", "etiqueta": "revisar"}
   ]
   ```

3. Envía el lote. Verás dos veredictos: la primera venta **APROBAR** (sin
   evidencia de defecto, costo esperado S/ 1,53, por debajo del costo de revisar)
   y la segunda **REVISAR** con la regla `R31` (recibo físico no declarado): se
   prometió S/ 99 "todo incluido" y el recibo físico agrega S/ 10, total
   S/ 109. Cada una con su cadena de evidencia, fuente y contrafáctico; abajo, la
   matriz de confusión contra las etiquetas.

No se cae con columnas desconocidas ni con filas corruptas: las reporta y sigue.

---

## 5. Qué es real y qué es simulado

**Real — corre de verdad, sin red y sin credenciales:**

- El motor de reglas (39 reglas sobre las seis aristas del rombo y las señales),
  la ingesta tolerante, el cálculo de costo esperado, el contrafáctico, el flujo
  de confirmación por enlace y la bandeja de avisos. Todo funciona de punta a
  punta con datos que el propio jurado ingresa.
- El banco de 24 casos adversarios (`data/casos-adversarios.json`) se clasifica
  **24/24**: cada `pasa`, `revisar` y `abstención` esperado coincide con el
  veredicto obtenido y con la regla principal del caso.
- La capa de IA (extracción, mapeo, redacción y resumen) corre de verdad con
  OpenCode Go; ver *IA aplicada*.

**Simulado — nunca se presenta como dato real de WIN:**

- Todos los datos personales (nombres, documentos, teléfonos, correos,
  direcciones) son generados.
- El catálogo de planes, promos, precios y cobertura, los costos de cada
  desenlace, los priors y las ventanas viven en `config/*.yaml`, marcados
  `origen: SUPUESTO_DEMO` con su fuente. La interfaz muestra ese origen junto a
  cada regla que se dispara.

No hay ningún dato sintético presentado como real.

---

## IA aplicada

La capa de IA está implementada y corre de verdad: proveedor **OpenCode Go**
(endpoint compatible con OpenAI en `https://opencode.ai/zen/go/v1`), modelo por
defecto `deepseek-v4-flash`. La IA **extrae, mapea y explica; nunca decide por sí
sola**: la decisión sigue saliendo del motor de reglas y del costo esperado, de
modo que la explicabilidad es estructural y no depende del modelo.

Se usa en cinco puntos, siempre **una llamada por lote, nunca por fila**, con la
explicación por veredicto cacheada:

1. **Normaliza la promesa** en lenguaje natural a estructura (plan, precio,
   velocidad, promoción, plazo) y detecta **claims sin respaldo en el catálogo**
   más allá del léxico. Esos claims se marcan `origen IA` y alimentan la regla
   `R23` (promesa insostenible).
2. **Mapea columnas desconocidas** del lote del jurado a campos conocidos; en el
   reporte de ingesta aparecen como `mapeado por IA`.
3. **Redacta "Por qué, en palabras"** en cada veredicto, citando solo las reglas
   y los valores que realmente se dispararon; la salida se valida contra la
   evidencia y se rechazan reglas o números que no estén en ella.
4. **"Lectura del lote"**: resumen del lote con patrones transversales y la
   prioridad de revisión.
5. **Texto en lenguaje llano para el cliente** en el enlace de confirmación.

Sin clave o sin red nada se cae: el sistema degrada al comparador determinista y
la interfaz lo indica ("IA no disponible: comparador determinista"). Ver
*Variables de entorno*.

---

## 6. Contrato de datos y ruta de adopción

El detalle de campos, frecuencia, mecanismo de entrega, degradación y
minimización de datos está en **[CONTRATO-DE-DATOS.md](CONTRATO-DE-DATOS.md)**.

### Ruta de adopción

| Etapa | Quién lo usa | Con qué se conecta | Desde cuándo | Qué debe existir del lado de WIN |
|---|---|---|---|---|
| 0 · Demo autónoma | Calidad de venta (carga de lotes y revisión) | nada | día uno | nada: corre local o en URL pública, sin red |
| 1 · Registro en línea | Calidad de venta + despacho | registro de venta (CRM) por API | semana 1–2 | una API que exponga el registro al cerrar la venta (`id`, vendedor, canal, cliente, teléfono, correo, dirección, distrito, plan, precio, promo, fechas, consentimiento) |
| 2 · Promesa y reedición | Formulario de venta + calidad | formulario (campos nuevos `promise_text`, `fill_seconds`) + CDC de ediciones | semana 2–4 | capturar la promesa como dato y publicar cada edición del registro (captura de cambios) |
| 3 · Cierre del arco | Calidad, despacho, facturación, atención | webhooks de despacho (`install_date`, `resultado_instalacion`), facturación (`primera_factura`) y atención (`baja_90_dias`) | mes 1–2 | emitir los hechos del arco como eventos fechados, no como estados que se sobrescriben |

En cada etapa el sistema se calibra con datos reales: el catálogo, los costos y
los priors dejan de ser supuestos de demo.

---

## 7. Quiénes somos y qué construyó cada uno

| Integrante | Rol | Responsable de |
|---|---|---|
| Roger Zavaleta Marcelo | Motor | reglas, comparadores, costo esperado, señales, contrafáctico (`/engine`) |
| Abraham Vidaurre Serpa | Superficie | ingesta del lote, vistas, veredicto, datos sintéticos (`/app`) |
| Jonatan Ching Ayacila | Circuito | confirmación del cliente, capa de aviso, contrato de datos, despliegue, guion (`/confirm`, `/docs`) |

El contrato entre las tres carpetas es el tipo compartido de `/contracts`,
congelado al cerrar la fase 1.

---

## Documentos

Los cinco entregables del equipo y los del prototipo viven juntos en el repo:

| Documento | Qué es |
|---|---|
| `docs/RETO-03-FUENTE.md` | Enunciado y rúbrica oficiales del reto, citados en literal |
| `docs/EVIDENCIA-PUBLICA.md` | Cartilla, contrato, Anexo 1 y OSIPTEL, con fuente exacta |
| `docs/MODELO-DE-COSTO.md` | Parámetros `P-NN`, cuatro desenlaces y umbral de decisión |
| `docs/CASOS-ADVERSARIOS.md` | Banco de 24 casos adversarios (buenas, defectuosas, ambiguas, límite) |
| `CONTRATO-DE-DATOS.md` | 30 campos, mecanismo de entrega, degradación y minimización |
| `config/*.yaml` | Reglas R01–R39, catálogo (tres superficies), costos, léxico y ventanas |
| `engine/` · `app/` · `confirm/` | Motor, superficie web y circuito de confirmación |
| `data/cases.json` | 25 casos sintéticos de demo |
| `data/casos-adversarios.json` | Espejo del banco, listo para cargar en `/lote` |
| `tests/` | 97 tests (motor, ingesta, IA, app y banco adversario) |

---

## Cómo correrlo local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000`.

## Cómo desplegar

- **Docker:** `docker build -t win-reto03 .` y `docker run -p 8000:8000 win-reto03`.
- **Render:** el repo incluye `render.yaml` (servicio web free, runtime Docker,
  health check en `/salud`).
- **Fly.io:** el repo incluye `fly.toml`; ejecuta `fly deploy`.

El estado vive en `data/state.json`: en instancias free es efímero. Para que
sobreviva a reinicios, monta un volumen en esa ruta.

## Variables de entorno

- `OPENCODE_API_KEY` — **opcional**. Clave del proveedor OpenCode Go. En local
  también se lee de `~/.local/share/opencode/auth.json`.
- `LLM_MODEL` — **opcional**. Modelo de OpenCode Go; por defecto
  `deepseek-v4-flash`.
- `ANTHROPIC_API_KEY` — **opcional**. Alternativa (modelo `claude-opus-5`); tiene
  prioridad sobre OpenCode Go.
- `LLM_DISABLE=1` — apaga la IA por completo.

Prioridad: Anthropic → OpenCode Go → comparador determinista. Sin clave, sin red
o ante cualquier error, el sistema degrada al comparador determinista y **lo dice
en pantalla**. Ninguna llamada externa es obligatoria.

## Gates

```bash
.venv/bin/python -m compileall -q contracts engine app confirm
.venv/bin/pytest -q
.venv/bin/python -c "from app.main import app; print('app-ok')"
```
