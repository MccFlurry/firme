# Firme

**Que lo prometido sea lo entregado.**

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

Firme trata la **promesa** como objeto de primera clase: en lugar de puntuar
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
2. Pega este lote. Usa un **esquema distinto al interno** a propósito: las
   columnas se llaman `customer`, `phone_number`, `monthly_price` y `plan_name`,
   y la ingesta las mapea por nombre aproximado.

   ```json
   [
     {"customer": "Ana Quispe",  "phone_number": "912345678", "monthly_price": 79.90, "plan_name": "Fibra 200", "label": "buena"},
     {"customer": "Luis Paredes","phone_number": "923456789", "monthly_price": 50.00, "plan_name": "Fibra 400", "label": "mala"}
   ]
   ```

3. Envía el lote. Verás dos veredictos: la primera venta **APROBAR** y la segunda
   **REVISAR** (precio S/ 50 por debajo del tarifario de Fibra 400), cada una con
   su cadena de evidencia, costo esperado y contrafáctico; abajo, la matriz de
   confusión contra las etiquetas.

No se cae con columnas desconocidas ni con filas corruptas: las reporta y sigue.

---

## 5. Qué es real y qué es simulado

**Real — corre de verdad, sin red y sin credenciales:**

- El motor de reglas (29 reglas sobre las seis aristas del rombo y las señales),
  la ingesta tolerante, el cálculo de costo esperado, el contrafáctico, el flujo
  de confirmación por enlace y la bandeja de avisos. Todo funciona de punta a
  punta con datos que el propio jurado ingresa.

**Simulado — nunca se presenta como dato real de WIN:**

- Todos los datos personales (nombres, documentos, teléfonos, correos,
  direcciones) son generados. Marca de agua `SIMULADO` en todas las pantallas.
- El catálogo de planes, promos, precios y cobertura, los costos de cada
  desenlace, los priors y las ventanas viven en `config/*.yaml`, marcados
  `origen: SUPUESTO_DEMO` con su fuente. La interfaz muestra ese origen junto a
  cada regla que se dispara.

No hay ningún dato sintético presentado como real.

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

## Cómo correrlo local

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000`.

## Cómo desplegar

- **Docker:** `docker build -t firme .` y `docker run -p 8000:8000 firme`.
- **Render:** el repo incluye `render.yaml` (servicio web free, runtime Docker,
  health check en `/salud`).
- **Fly.io:** el repo incluye `fly.toml`; ejecuta `fly deploy`.

El estado vive en `data/state.json`: en instancias free es efímero. Para que
sobreviva a reinicios, monta un volumen en esa ruta.

## Variables de entorno

- `ANTHROPIC_API_KEY` — **opcional**. Si está definida, la capa LLM normaliza la
  promesa y redacta la explicación al cliente. Sin ella (o sin red, o ante
  cualquier error) el sistema degrada a un comparador determinista y **lo dice en
  pantalla**. Ninguna llamada externa es obligatoria.

## Gates

```bash
.venv/bin/python -m compileall -q contracts engine app confirm
.venv/bin/pytest -q
.venv/bin/python -c "from app.main import app; print('app-ok')"
```
