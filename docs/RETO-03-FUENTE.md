# Reto 03 — Fuente de verdad

> **Idioma:** este archivo está en español porque cita literalmente el material
> oficial del concurso. No traducir: cualquier reformulación corrompe la fuente.
>
> **Origen:** `Retos_Hackaton_WIN_Chiclayo_v3.pptx`, láminas 2, 5 y 7. Texto
> extraído del XML del archivo, no transcrito a mano.
>
> **Uso:** toda decisión de diseño en este repositorio debe poder trazarse a una
> frase de este documento. Si una idea no se traza acá, se descarta.

---

## 1. Enunciado oficial — lámina 5, literal

**RETO 03 · ÁREA DUEÑA: CALIDAD DE VENTA · VENTAS · EXPERIENCIA CLIENTE**

**QUE LO PROMETIDO SEA LO ENTREGADO**

**LA PREGUNTA**

> ¿Cómo verificamos que cada venta que entra fue hecha como debe ser, con el
> cliente correcto y con la promesa correcta, antes de que se convierta en una
> instalación, una factura y un problema?

**POR QUÉ DUELE**

> Una venta que no fue lo que parecía no se paga en la venta. Se paga después:
> instalación fallida, un cliente que nunca pidió el servicio, reclamo, baja
> temprana y un costo que ya no se recupera.

**CON QUÉ SE TRABAJA**

> Tarifario y condiciones públicas, los arquetipos que describan los mentores
> comerciales, y lo que el equipo levante conversando con vendedores.

**DENTRO DEL CAMPO**

> Todo el arco desde el primer contacto hasta la primera factura: cómo se
> registra la venta, cómo se valida quién está del otro lado, qué señales
> delatan una venta que no se sostiene, y cómo se le avisa a alguien a tiempo.

**FUERA DEL CAMPO**

> Bajar el precio o cambiar la comisión. Si la respuesta es un incentivo
> distinto, no respondió la pregunta.

**CÓMO SE JUZGA**

> Que sobre un lote de casos preparado por el jurado, con ventas buenas y ventas
> que no lo eran, la propuesta separe unas de otras y explique en qué se basó.

---

## 2. Rúbrica oficial — lámina 7, literal

> El jurado representa la visión de cada área. **Un prototipo modesto que
> responde la pregunta gana a una demo espectacular que no la responde.**

| Criterio | Qué miran | Peso |
|---|---|---|
| **Entendimiento del problema** | Que el equipo haya entendido el negocio real, no la versión que imaginó. Se nota en las preguntas que le hicieron al mentor. | **20%** |
| **Originalidad del enfoque** | Que el camino no sea el primero que aparece: ángulos distintos, señales no obvias, replanteos del problema. | **20%** |
| **Prototipo, no maqueta** | Algo que corre y se puede probar en vivo, aunque sea parcial. Un video y unas láminas no son un prototipo. | **25%** |
| **Aplicabilidad en WIN** | Contrato de datos completo y una ruta de adopción creíble: qué área lo usaría, con qué, y desde cuándo. | **25%** |
| **Claridad al presentar** | Cinco minutos. Que se entienda qué construyeron, por qué así, y qué pasaría si WIN lo adopta. | **10%** |

### El contrato de datos — obligatorio en los cuatro retos

> Una página: qué campos necesitaría de WIN para operar en producción, con qué
> frecuencia y qué pasa si no los tiene. Es lo que convierte el prototipo en algo
> integrable, y de paso le dice a WIN qué información debería estar exponiendo
> internamente.

---

## 3. Contexto del concurso — lámina 2

> Cuatro preguntas abiertas · Sin data interna · Entregables que WIN puede usar.
>
> Cada equipo elige una. Ningún reto se abre con menos de dos equipos: sin
> comparación no hay ganador, hay único.
>
> **Cuatro preguntas, cero soluciones prescritas.** El reto dice qué resolver y
> cómo se mide. Nunca cómo hacerlo.

Los otros tres retos (01 medición de señal en casa, 02 escucha social, 04
comercialización de cobertura wifi) no son competencia directa: el reto 03 se
compara contra los demás equipos que eligieron el reto 03.

---

## 4. Lectura del enunciado — decisiones ya tomadas por el equipo

Tres frases del enunciado son requisitos funcionales, no contexto decorativo:

1. **«con el cliente correcto»** + **«un cliente que nunca pidió el servicio»** +
   **«cómo se valida quién está del otro lado»** → el reto exige verificación de
   **consentimiento e identidad del titular**, no solo validación tarifaria.
2. **«todo el arco desde el primer contacto hasta la primera factura»** → el
   alcance incluye lo previo (qué se prometió) y lo posterior (instalación,
   primera factura, baja temprana) como fuente de etiquetas.
3. **«cómo se le avisa a alguien a tiempo»** → se exige una capa de aviso con
   destinatario, canal, urgencia y ventana. Un tablero que nadie abre no avisa.

### Tesis del producto

> **La unidad de análisis no es la venta registrada. Es la promesa.**

El defecto no vive en el registro: vive en la distancia entre lo que se le dijo
al cliente y lo que el sistema va a entregarle. De ahí el rombo de comparadores:

```
  PROMESA DECLARADA      lo que el vendedor dice que ofreció
          ↕
  CATÁLOGO VIGENTE       lo que comercialmente existe y es combinable
          ↕
  REGISTRO DE VENTA      lo que quedó escrito en el sistema
          ↕
  ENTREGABLE REAL        lo que se va a instalar y a facturar
```

Un defecto es un desacuerdo entre dos nodos del rombo.

### Los cuatro pilares

- **(A)** La promesa como objeto de primera clase, capturada y normalizada.
- **(B)** El cliente es el verificador: enlace de confirmación antes de la
  instalación. El silencio del cliente es señal.
- **(C)** Decisión por **costo esperado en soles**, no por score 0–100. El umbral
  es donde el costo esperado del defecto supera el costo de revisar.
- **(D)** Dos ejes —severidad × fuerza de evidencia— con derecho a abstenerse.

### La ventana

Toda detección que llega después de que sale el camión vale cero. El sistema
opera en la ventana entre venta e instalación (supuesto: 24–72 h,
parametrizable, **pendiente de confirmar con el mentor**).

### Posicionamiento

El área dueña es **VENTAS**. Un producto que se presenta como policía del
vendedor genera rechazo en quien más puntúa. Encuadre correcto: protege las
ventas buenas de quedar atrapadas en revisión, protege al cliente de una promesa
que no se sostiene, y protege al vendedor honesto de cargar con el costo del que
no lo es.

---

## 5. Restricciones que no se negocian

1. **Fuera del campo, literal:** no proponer bajar precios, cambiar comisiones,
   ni ningún esquema de incentivos como solución. Se puede *medir* patrones
   asociados a incentivos; no se puede proponer modificarlos.
2. **Cero políticas comerciales inventadas de WIN.** Todo umbral, precio,
   promoción, condición y costo se marca `origen: SUPUESTO_DEMO` u
   `origen: PÚBLICO` con su fuente.
3. **Cero datos personales reales.** Todo caso es sintético y va marcado
   `SIMULADO`. Nunca presentar dato sintético como dato real de WIN.
4. **Sin acceso a sistemas internos de WIN**, CRM, APIs privadas ni base de
   clientes.

---

## 6. Alcance de este repositorio

Este repositorio contiene **solo los entregables que no son código**. El
prototipo de software lo construye un tercer integrante en otra vía, con
Claude Fable 5.1. Los entregables de acá son insumo suyo, no dependen de él.

| Entregable | Criterio que puntúa |
|---|---|
| `CONTRATO-DE-DATOS.md` | Aplicabilidad en WIN — 25% |
| `docs/CASOS-ADVERSARIOS.md` | Prototipo (lo endurece) + originalidad |
| `docs/MODELO-DE-COSTO.md` | Aplicabilidad + originalidad (pilar C) |

---

## 7. Supuestos abiertos — confirmar con el mentor comercial

Ninguno de estos está confirmado. Cada documento que dependa de uno debe
marcarlo explícitamente.

- Ventana real entre registro de venta e instalación.
- Costo de una instalación fallida (visita técnica sin falla atribuible).
- Costo de una baja dentro de los primeros 90 días.
- Costo y capacidad de una revisión manual de venta (minutos por caso, quién).
- Volumen diario de ventas que entran por cada canal.
- Qué campos existen hoy en el registro de venta y cuáles no.
- Si existe hoy alguna traza de consentimiento del cliente.
