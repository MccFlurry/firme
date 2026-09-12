# Contrato de datos

Firme · Hackatón WIN Chiclayo 2026 · Reto 03

Documento de nivel producción: describe qué campos necesita Firme para operar,
de qué sistema salen, con qué frecuencia, y qué pasa si no están. No es una lista
de deseos: por cada campo ausente se especifica el modo de degradación.

Los sistemas de origen se nombran por su rol lógico (registro de venta,
facturación, despacho, atención). Los nombres concretos de los sistemas internos
de WIN se confirmarán con el área dueña; lo que este documento compromete es
*qué información* debe existir y *con qué latencia*, no el nombre del sistema.

---

## 1. Campos y su contrato

### Identidad y titularidad

| Campo | Descripción | Tipo | Sistema origen | Frecuencia | Latencia máxima tolerable | Obligatorio | Si falta, qué pasa |
|---|---|---|---|---|---|---|---|
| `id` | Identificador único de la venta | texto | registro de venta | en el acto | en el acto | Sí | Si el origen no lo trae, se genera uno en la ingesta; se pierde trazabilidad contra el CRM. |
| `customer_name` | Nombre del cliente | texto | registro de venta | en el acto | en el acto | Sí (para el flujo humano) | Se pierde la comparación de nombre en colisiones y la pantalla del cliente queda sin saludo. No cambia la decisión de precio/cobertura. |
| `customer_doc` | Documento de identidad | texto (seudonimizado) | registro de venta | en el acto | en el acto | Sí | Se pierde la colisión por documento. Si además faltan teléfono y correo, el sistema se **abstiene** (no hay identificador de cliente). |
| `phone` | Teléfono | texto (seudonimizado) | registro de venta | en el acto | en el acto | Sí | Se pierde la colisión por teléfono y el envío del enlace de confirmación. Sin documento ni correo, se **abstiene**. |
| `email` | Correo | texto (seudonimizado) | registro de venta | en el acto | en el acto | No | Se pierde la colisión por correo y una vía de confirmación. Degradación baja. |
| `address` | Dirección de instalación | texto (hash normalizado) | registro de venta | en el acto | en el acto | No | Se pierde la colisión por dirección repetida. Degradación baja. |
| `district` | Distrito o zona | texto (id de zona) | registro de venta | en el acto | en el acto | Sí | Se pierde toda la arista registro–entrega (cobertura/velocidad). Degradación alta: no se puede verificar que la zona soporta el plan. |
| `consent_evidence` | Evidencia de consentimiento (grabación, firma, SMS) | enumerado | registro de venta / grabación | en el acto | en el acto | No (la ausencia es señal) | Si el campo existe y llega vacío, dispara la señal de identidad por diseño y empuja hacia REVISAR. Si el sistema origen no expone el campo, la señal no se calcula y se reporta como campo faltante. |

### Vendedor y canal

| Campo | Descripción | Tipo | Sistema origen | Frecuencia | Latencia máxima tolerable | Obligatorio | Si falta, qué pasa |
|---|---|---|---|---|---|---|---|
| `seller_id` | Identificador del vendedor | texto | registro de venta | en el acto | en el acto | Sí | Se pierde la señal de ráfaga (≥3 ventas en 10 min) y la cohorte por vendedor. Degradación baja-media. |
| `channel` | Canal (call center, campo, web, tienda) | enumerado | registro de venta | en el acto | en el acto | Sí | Se usa el prior por defecto en lugar del prior del canal. Degradación baja (calibración bayesiana). |

### Promesa y registro

| Campo | Descripción | Tipo | Sistema origen | Frecuencia | Latencia máxima tolerable | Obligatorio | Si falta, qué pasa |
|---|---|---|---|---|---|---|---|
| `promise_text` | Promesa en lenguaje natural (qué se le dijo al cliente) | texto libre | nota de venta / transcripción / captura nueva | en el acto | en el acto | No | Se pierde la arista de promesa (promesa↔catálogo y promesa↔registro). El sistema degrada a comparar solo catálogo↔registro y lo declara. |
| `plan` | Plan ofertado (id del catálogo) | texto (id) | registro de venta | en el acto | en el acto | Sí | Sin plan **y** sin precio, el sistema se **abstiene**. Con precio pero sin plan, se pierde la comparación contra el catálogo y la cobertura. |
| `price` | Precio mensual registrado (S/) | numérico | registro de venta | en el acto | en el acto | Sí | Sin precio **y** sin plan, se **abstiene**. Con plan pero sin precio, se pierde la regla de precio bajo tarifa y parte del costo esperado. |
| `promo` | Promoción aplicada (id del catálogo) | texto (id) | registro de venta | en el acto | en el acto | No | Se pierden las reglas de promoción (aplicabilidad y combinación). Degradación media. |
| `install_date` | Fecha de instalación | fecha | despacho e instalaciones | al agendar | dentro de la ventana | No | Sin fecha, el plazo de la bandeja usa `now + ventana − margen`. Se pierde el plazo real y la arista de ventana de instalación. |
| `registered_at` | Fecha y hora de registro | fecha-hora | registro de venta | en el acto | en el acto | Sí | Se pierde la señal de hora fuera de patrón; la ráfaga se degrada (sin orden temporal). |
| `fill_seconds` | Tiempo de llenado del formulario | numérico | formulario (medido en el navegador) | en el acto | en el acto | No | Se pierde la señal de llenado anormalmente corto. Degradación baja. |
| `edits` | Historial de ediciones (campo, antes, después) | lista | registro de venta (CDC) | al ocurrir | en el acto | No | Se pierde la señal de reedición (precio editado ≥2 veces, identidad editada tras enviar). Degradación media. |

### Entregable y etiquetas del arco

Estos campos no alimentan la decisión en línea; son las **etiquetas** con las que
el sistema se calibra y valida su propio modelo de costo.

| Campo | Descripción | Tipo | Sistema origen | Frecuencia | Latencia máxima tolerable | Obligatorio | Si falta, qué pasa |
|---|---|---|---|---|---|---|---|
| `resultado_instalacion` | Resultado de la instalación (exitosa, fallida, no contactada) | enumerado | despacho e instalaciones | al cerrar la orden | 7 días | No | Sin él no hay bucle de aprendizaje sobre instalaciones fallidas; la decisión no se degrada. |
| `primera_factura` | Monto y fecha de la primera factura emitida | numérico + fecha | facturación | al emitir | 7 días | No | Sin él no se valida registro↔facturación; la decisión no se degrada. |
| `baja_90_dias` | Si el cliente se dio de baja dentro de 90 días | booleano | atención / facturación | al ocurrir (CDC) o a los 90 días | 90 días | No | Sin él no se mide baja temprana; la decisión no se degrada. |

---

## 2. Mecanismo de entrega por campo

| Campo | Mecanismo |
|---|---|
| `id`, `seller_id`, `channel`, `customer_*`, `phone`, `email`, `address`, `district`, `plan`, `price`, `promo`, `registered_at`, `consent_evidence` | **API** en el acto de la venta (o export del CRM al cerrar el registro). Son datos que existen al momento de registrar. |
| `promise_text` | **API / captura nueva**: si el origen no tiene nota libre, se captura como campo nuevo en el formulario. |
| `fill_seconds` | **Captura en el navegador**: se mide en el cliente y viaja junto con el registro. |
| `edits` | **CDC** (captura de cambios) sobre el registro de venta: cada edición se envía al ocurrir. |
| `install_date`, `resultado_instalacion` | **Webhook** desde despacho e instalaciones: al agendar y al cerrar la orden. |
| `primera_factura` | **Webhook** desde facturación al emitir, o **lote nocturno** de conciliación. |
| `baja_90_dias` | **Lote nocturno** de bajas del día, o **CDC** si el origen lo soporta. |

---

## 3. Modo de degradación por campo ausente

Regla general: el sistema **se abstiene** (no emite veredicto) cuando faltan
`plan` **y** `price`, o cuando no hay ningún identificador de cliente
(`customer_doc`, `phone` o `email`). El resto de las ausencias degrada señales
puntuales y se declara en pantalla como campos faltantes.

| Campo ausente | Señales que dejan de calcularse | Efecto sobre la decisión |
|---|---|---|
| `promise_text` | lingüística, promesa↔catálogo, promesa↔registro | Pierde dos aristas del rombo; queda catálogo↔registro + señales no obvias. |
| `plan` o `price` | promesa↔catálogo, catálogo↔registro, cobertura | Si faltan ambos → **abstenerse**. Si falta uno, decisión con más ruido y menos aristas. |
| `district` | registro↔entrega (cobertura/velocidad) | No se puede verificar compatibilidad técnica; degradación alta. |
| `consent_evidence` | identidad (ausencia) | Valor vacío: dispara la señal y empuja hacia REVISAR. Campo no expuesto por el origen: la señal no se calcula y se declara como faltante. |
| `phone`/`email`/`customer_doc` | colisiones, confirmación | Sin los tres → **abstenerse**. Falta parcial: se pierde una vía de confirmación y una colisión. |
| `edits` | reedición | Se pierde la señal de precio/identidad editados. |
| `registered_at` | hora fuera de patrón, ráfaga | La ráfaga se degrada a conteo sin orden temporal. |
| `fill_seconds` | llenado anormal | Se pierde una señal temporal. |
| `seller_id` | ráfaga, cohorte por vendedor | Se pierde la ráfaga por vendedor y la calibración individual. |
| `channel` | prior por canal | Se usa prior por defecto. |
| `install_date` | plazo de bandeja, ventana de instalación | El plazo usa un valor por defecto; la bandeja sigue operando con margen estimado. |
| Etiquetas (`resultado_instalacion`, `primera_factura`, `baja_90_dias`) | bucle de aprendizaje | La decisión en línea no se degrada; el modelo deja de recalibrarse. |

---

## 4. Minimización de datos personales

Firme no necesita ver los datos completos de una persona para detectar que
una promesa no se sostiene. Pedimos lo mínimo y seudonimizamos lo que se puede.

**Qué pedimos y por qué:**

- Identificador de cliente (documento, teléfono o correo): necesario para
  detectar colisiones (el mismo dato en clientes distintos) y para enviar el
  enlace de confirmación. Se **seudonimiza** en el repositorio.
- Nombre: necesario solo para el saludo de la pantalla del cliente y para
  detectar colisiones de nombre. Se **reduce a iniciales** en almacenamiento.
- Dirección: necesaria para la colisión por dirección repetida y para la
  cobertura por distrito. Se **almacena como hash normalizado** (minúsculas, sin tildes ni
  puntuación, espacios colapsados); el distrito se conserva en claro porque es
  un dato técnico de cobertura, no identificador.
- Documento de identidad: solo se usa como clave de colisión. Se **almacena como hash**.

**Qué no pedimos pudiendo pedirlo:**

- No pedimos historial de consumo, deuda ni datos de navegación del cliente.
- No pedimos datos biométricos más allá de la evidencia de consentimiento que ya
  existe en el origen.
- No retenemos el texto completo del documento ni el nombre completo más allá de
  la duración del veredicto; el enlace de confirmación no expone el documento.

**Retención:** los datos personales seudonimizados se retienen lo mínimo para el
ciclo de verificación y calibración; las etiquetas del arco se conservan de forma
agregada, no individual.

---

## 5. Qué debería exponer WIN internamente y hoy probablemente no

Redactado como recomendación de arquitectura de información, no como queja.

El arco del reto va del primer contacto a la primera factura, pero hoy esos
momentos viven en sistemas distintos que no se hablan. Para que cualquier
sistema de calidad de venta —no solo Firme— pueda operar, WIN necesita
exponer tres hechos que hoy probablemente no están disponibles como eventos:

1. **La promesa, como dato y no como nota.** Lo que se le dijo al cliente debe
   existir de forma capturable (texto estructurado o transcripción), no solo como
   comentario libre imposible de comparar. Sin esto, el rombo no tiene la arista
   más valiosa.
2. **Un identificador de cliente consistente entre sistemas.** El mismo teléfono,
   documento o correo debe poder compararse entre ventas, facturación y atención
   para detectar colisiones y duplicados. Hoy cada sistema probablemente guarda
   su propia versión.
3. **Eventos del arco como hechos fechados.** La instalación, la primera factura
   y la baja temprana deben poder consultarse como eventos con fecha y resultado,
   no como estados que se sobrescriben. Son las etiquetas que cierran el bucle
   de aprendizaje.

La recomendación no es construir un nuevo sistema, sino **exponer** estos tres
hechos por API o por lotes con latencia conocida. Esa exposición es el habilitador
más barato y de mayor retorno para toda la función de calidad de venta.

---

## 6. Qué funciona en el día uno sin nada de WIN, y qué requiere integración

**Funciona desde el día uno, sin integración con WIN:**

- La ingesta del lote del jurado (pegar o subir JSON/CSV, o llenar el formulario).
- El motor de reglas, el catálogo de supuestos y el costo esperado, corriendo
  sobre los datos que el propio usuario ingresa.
- Las señales no obvias provocables desde el formulario (ráfaga, llenado, hora,
  reedición, colisión, lingüística, ausencia).
- La confirmación del cliente por enlace y la bandeja de avisos.
- Todo funciona sin red y sin clave de LLM (degrada a comparador determinista).

**Requiere integración con WIN:**

- Alimentar `plan`, `price`, `promo`, `district`, `customer_*` y
  `consent_evidence` desde el registro real de venta (API en el acto).
- Recibir `edits` por CDC para la señal de reedición real.
- Recibir `install_date` y `resultado_instalacion` desde despacho, y
  `primera_factura` / `baja_90_dias` desde facturación y atención, para cerrar
  el bucle de aprendizaje con etiquetas reales.
- Validar el catálogo, los costos y los priors contra la operación real, para
  que los parámetros dejen de ser supuestos de demo.

La ruta de adopción por etapas está detallada en el `README.md`.
