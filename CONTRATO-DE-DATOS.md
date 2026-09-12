# Contrato de datos

**Qué necesitamos de WIN para operar en producción, con qué frecuencia, y qué
deja de funcionar si no lo tenemos.**

---

## 1. La respuesta, en una línea

El sistema necesita **30 campos**. **21 ya están impresos en el formulario de
venta de WIN** (Anexo 1 del contrato de servicio), 4 son derivables de lo que ya
existe, y **5 no existen hoy**. Sin esos 5, el sistema sigue validando precio,
producto y condiciones comerciales; lo que pierde es la capacidad de verificar
**la promesa** y **quién está del otro lado** — es decir, media pregunta del
reto.

## 2. Lo que WIN ya tiene y lo que falta

| | Campos | Qué significa |
|---|---|---|
| **Total requerido** | 30 | El contrato completo |
| **Literal del Anexo 1** | 21 | WIN ya los captura hoy, en papel. Día 1 sin integración nueva |
| **Derivable de lo existente** | 4 | Se obtienen de campos actuales. Requieren confirmación, no desarrollo |
| **No existe hoy** | 5 | Requieren decisión de WIN. Son los que habilitan la verificación de promesa e identidad |

## 3. Si falta, qué se apaga

Tres niveles. El sistema **degrada, no se apaga**: cada nivel deja en pie lo que
todavía puede sostener con evidencia.

| Nivel | Si falta | Comparadores que dejan de calcular | Veredicto disponible |
|---|---|---|---|
| **1** | Solo los 5 campos nuevos | `PROMESA ↔ CATÁLOGO` y `PROMESA ↔ REGISTRO` | `pasa` / `revisar` sobre consistencia comercial. Nunca `revisar` por promesa o consentimiento |
| **2** | Además, los 4 derivables | Señales de cohorte por canal y zona | `pasa` / `revisar` solo sobre el registro contra el catálogo |
| **3** | Campos obligatorios del Anexo 1 incompletos | `CATÁLOGO ↔ REGISTRO` | `abstención`. El sistema declara que no tiene con qué decidir |

El nivel 3 no es una falla: es la respuesta correcta cuando no hay evidencia.
Ver `docs/MODELO-DE-COSTO.md` §5.

---

*Hasta acá, la respuesta. Lo que sigue es su evidencia.*

---

## 4. Campos

Ocho atributos por campo. Los que son constantes dentro de un bloque están en el
encabezado del bloque, no repetidos fila por fila.

La columna **«Si falta, qué pasa»** sigue una gramática fija de tres partes:

```
<comparador o desenlace que deja de calcular> → <veredicto degradado> → <la ausencia es señal: sí | no>
```

Un valor como «el modelo pierde precisión» no es admisible en esa columna. Si no
se puede nombrar qué deja de calcular, el campo no está justificado.

### Bloque A — Literal del Anexo 1

> **Sistema origen:** Anexo 1 del contrato de servicio (`PÚBLICO-WIN`) para toda
> fila del bloque. **Frecuencia:** por evento de venta. **Latencia máxima
> tolerable:** 24 h desde el registro — la ventana contractual de instalación es
> `P-01` (`PÚBLICO-WIN`), de modo que hay margen; llegar el mismo día permite
> corregir antes de agendar la visita.

| Campo | Descripción | Tipo | Oblig. | Si falta, qué pasa |
|---|---|---|---|---|
| `velocidad_contratada` | Velocidad del plan vendido | entero (Mbps) | Sí | `CATÁLOGO ↔ REGISTRO` → `abstención` → no |
| `precio_mensual` | Renta mensual pactada | decimal (S/) | Sí | `CATÁLOGO ↔ REGISTRO` → `abstención` → no |
| `plazo_estimado_instalacion` | Días hasta instalación. Preimpreso en `P-01` | entero (días) | Sí | Ventana de intervención → `revisar` por defecto → no |
| `forma_pago_instalacion` | Momento de cobro del cargo de instalación | enum | Sí | `REGISTRO ↔ ENTREGABLE` sobre primera factura → `pasa` sin ese chequeo → no |
| `cargo_instalacion_costo` | Cargo de instalación. Valor publicado: `P-02` (`PÚBLICO-WIN`) | decimal (S/) | Sí | `REGISTRO ↔ ENTREGABLE` sobre primera factura → `pasa` sin ese chequeo → no |
| `cargo_instalacion_cuotas` | Número de cuotas. Publicado: 6 (`P-02`, `PÚBLICO-WIN`) | entero | Sí | `REGISTRO ↔ ENTREGABLE` sobre primera factura → `pasa` sin ese chequeo → no |
| `forma_pago` | Mes vencido / adelantado | enum | Sí | Reversión de facturación → `pasa` sin ese chequeo → no |
| `forma_entrega_recibo` | Físico o electrónico. El físico agrega `P-03` (`PÚBLICO-WIN`) al total mensual | enum | **Sí** | `PROMESA ↔ ENTREGABLE` sobre el total facturado → `pasa` sin ese chequeo → **sí**, un vacío suele indicar valor por defecto no revisado |
| `plazo_vigencia` | Indeterminado o forzoso `P-04` (`PÚBLICO-WIN`) | enum | **Sí** | `PROMESA ↔ REGISTRO` sobre permanencia → `abstención` → **sí** |
| `direccion` | Dirección de instalación | texto | Sí | Cobertura y zona → `abstención` → no |
| `etapa` | Etapa o urbanización | texto | No | Precisión de zona → sin cambio de veredicto → no |
| `nombre_condominio` | Condominio, si aplica | texto | No | Colisión de dirección → esa señal no corre → no |
| `torre` | Torre, si aplica | texto | No | Colisión de dirección → esa señal no corre → no |
| `departamento` | Departamento, si aplica | texto | No | Colisión de dirección → esa señal no corre → no |
| `tenencia` | Propietario o inquilino | enum | **Sí** | Verificación de titularidad → `abstención` sobre identidad → **sí** |
| `telefono_1` | Contacto principal | texto | Sí | Envío de confirmación al titular → `abstención` sobre consentimiento → no |
| `telefono_2` | Contacto alterno | texto | No | Colisión de contacto entre clientes → esa señal no corre → no |
| `correo_electronico` | Correo del cliente | texto | No | Canal alterno de confirmación → sin cambio de veredicto → no |
| `nombre_asesor` | Asesor que registró la venta | texto | **Sí** | Cohorte por asesor → `revisar` sin calibración previa → **sí** |
| `equipo` | Equipo comercial del asesor | texto | Sí | Cohorte por equipo y canal → `revisar` sin calibración previa → **sí** |
| `cliente_documento` | Tipo y número de documento del firmante | texto | Sí | Colisión de identidad entre ventas → `abstención` sobre identidad → no |

`tenencia`, `plazo_vigencia`, `forma_entrega_recibo`, `nombre_asesor` y `equipo`
merecen atención: son campos que WIN **ya captura** y que hoy, hasta donde
sabemos, no se usan como señal de calidad de venta.

### Bloque B — Derivable de lo existente · marcar **confirmar**

> **Sistema origen:** registro de venta digital de WIN. **Estado:** no está
> confirmado que el registro digital tenga campos más allá del Anexo 1 impreso
> (`EVIDENCIA-PUBLICA.md` §9, punto 6). Estas filas se **proponen**, no se
> afirman.

| Campo | Descripción | Tipo | Frecuencia | Latencia | Oblig. | Si falta, qué pasa |
|---|---|---|---|---|---|---|
| `fecha_hora_registro` | Marca de tiempo del registro | timestamp | por venta | 24 h | Sí *(confirmar)* | Señal temporal fuera de patrón → `pasa` sin esa señal → no |
| `canal` | Canal de venta: presencial, telefónico, digital | enum | por venta | 24 h | Sí *(confirmar)* | Cohorte por canal → `revisar` sin calibración → no |
| `ediciones_registro` | Cuántas veces se corrigió el registro tras enviarlo, y qué campo | lista | por venta | 24 h | No *(confirmar)* | Señal de reedición → `pasa` sin esa señal → **sí** |
| `score_crediticio` | Evaluación crediticia. Mínimo publicado: 201 puntos (`PÚBLICO-WIN`, cartilla §2.3) | entero | por venta | 24 h | No *(confirmar)* | Condición de acceso publicada → `pasa` sin ese chequeo → **sí** |

### Bloque C — No existe hoy

> **Sistema origen:** ninguno. Requieren decisión de WIN. **Son los campos que
> habilitan la verificación de promesa e identidad**, es decir, la mitad del
> reto que no se resuelve validando tarifas.

| Campo | Descripción | Tipo | Frecuencia | Latencia | Oblig. | Si falta, qué pasa |
|---|---|---|---|---|---|---|
| `promesa_declarada` | Lo que el asesor declara haber ofrecido, en texto libre. Se normaliza contra el catálogo | texto | por venta | 24 h | Sí | `PROMESA ↔ CATÁLOGO` y `PROMESA ↔ REGISTRO` → `pasa` solo sobre consistencia comercial → no |
| `catalogo_referencia_id` | Identificador versionado del catálogo vigente al momento de la venta | texto | por cambio de catálogo | 24 h | Sí | `PROMESA ↔ CATÁLOGO` → **`abstención`** → no |
| `confirmacion_titular` | Estado de la confirmación del cliente. Ver §6 | enum | por venta | dentro de `P-07` | Sí | Verificación de consentimiento → `abstención` sobre identidad → **sí** |
| `confirmacion_titular_ts` | Momento de la respuesta del cliente | timestamp | por venta | dentro de `P-07` | Sí | Ventana de silencio → la ausencia deja de ser medible → **sí** |
| `acta_instalacion_ts` | Momento de firma del acta de instalación, artefacto que ya existe | timestamp | por instalación | 24 h | No | `REGISTRO ↔ ENTREGABLE` posterior → `pasa` sin ese cierre → no |

---

## 5. Mecanismo de entrega

| Grupo de campos | Canal | Frecuencia | Latencia máxima tolerable |
|---|---|---|---|
| Bloque A completo | Webhook por evento de venta, o lote cada 4 h | Por venta | 24 h desde el registro |
| Bloque B | Mismo canal que el bloque A | Por venta | 24 h |
| `catalogo_referencia_id` y el catálogo vigente | Publicación versionada, leída bajo demanda | Por cambio de catálogo | Inmediata al publicar |
| `confirmacion_titular` y su marca de tiempo | Escritura del propio sistema; devuelta a WIN por el mismo canal | Por respuesta del cliente | Dentro de `P-07` |
| `acta_instalacion_ts` | Lote diario | Por instalación | 24 h |

La ventana contractual de instalación es `P-01`. Una latencia de 24 h deja margen
para intervenir antes de agendar la visita técnica, que es el momento en que el
costo se vuelve irrecuperable.

> Definido en → `docs/MODELO-DE-COSTO.md` §3 (`P-01`, `P-07`).

## 6. Modo de degradación

Toda celda de la columna «Si falta, qué pasa» sigue la gramática de tres partes
declarada en la §4. La regla de fondo:

**Cuando falta la única evidencia que sostiene un veredicto, el veredicto es
`abstención`, no una suposición.** Un sistema que adivina cuando no sabe es peor
que uno que se abstiene, porque su error no se distingue de su acierto.

### El campo de consentimiento e identidad

`confirmacion_titular` es el ancla de identidad del sistema. Estados posibles:

| Estado | Significado |
|---|---|
| `no_enviada` | Todavía no se pidió confirmación |
| `enviada` | Se envió, aún dentro de la ventana |
| `no_respondida` | Venció la ventana sin respuesta |
| `confirmada` | El cliente reconoce la venta y la promesa |
| `confirmada_con_correccion` | El cliente reconoce la venta, pero corrige algo de lo prometido |
| `negada` | El cliente no reconoce la venta |

**`no_respondida` es un valor, no un vacío.** El silencio del cliente dentro de
la ventana es la señal más fuerte del sistema, y solo existe si se modela como
estado propio. Un campo nulo no se puede distinguir de un campo que nunca se
envió.

> Este es el campo que `docs/CASOS-ADVERSARIOS.md` cita en toda su familia de
> consentimiento. Nombre y estados se definen acá y no se renombran.

## 7. Minimización de datos

Ancla legal: contrato de servicio, **Cláusula Séptima (q)** — obligación de
observar el secreto de las telecomunicaciones y la confidencialidad de los datos
personales (`PÚBLICO-WIN`, `EVIDENCIA-PUBLICA.md` §3.3).

| Campo | Para qué se usa | Qué NO se pide, pudiendo pedirse |
|---|---|---|
| `cliente_documento` | Detectar colisión de identidad entre ventas distintas | El documento completo. Basta un identificador seudonimizado estable; el número real nunca sale del sistema de WIN |
| `telefono_1` | Enviar la confirmación al titular | Historial de llamadas, operador, cualquier dato de tráfico |
| `direccion` | Verificar cobertura y detectar colisión de dirección | Geolocalización, coordenadas, referencias del domicilio |
| `correo_electronico` | Canal alterno de confirmación | Cualquier uso comercial o de marketing |
| `tenencia` | Verificar titularidad declarada | Datos patrimoniales, títulos de propiedad, contratos de alquiler |
| `score_crediticio` | Verificar la condición de acceso ya publicada por WIN | El historial crediticio subyacente. Solo se necesita si supera el mínimo, no el detalle |

**Retención:** los campos de identidad se conservan solo mientras la venta esté
en la ventana de verificación. Cerrado el caso, se conserva el veredicto y su
evidencia, no los datos personales que lo produjeron.

Ningún dato de persona real se usa en este proyecto. Todo caso de prueba es
sintético y está marcado `SIMULADO`.

## 8. Qué debería exponer WIN internamente

Tres recomendaciones de arquitectura de información. Ninguna propone cambiar un
precio, una comisión ni un esquema de incentivos.

**Un catálogo comercial versionado, con identificador, como fuente única.**
Verificar que una promesa es correcta exige compararla contra un catálogo de
referencia. Hoy las condiciones publicadas y las páginas de venta describen
combinaciones distintas de plan, precio y promoción, y ninguna declara cuál
gobierna en un momento y una plaza determinados. **Mientras no exista ese
artefacto con identificador y versión, ninguna promesa puede validarse de forma
concluyente — ni por un sistema, ni por una persona, ni por el propio asesor.**
Es una brecha de arquitectura de información, y es la recomendación de mayor
impacto de este documento: exponer el catálogo vigente como dato versionado
habilita toda la verificación de promesa.

**La promesa declarada, capturada como dato.** Hoy lo que el asesor ofreció no
queda registrado en ninguna parte: solo queda lo que se registró. Sin ese campo
no hay forma de detectar la diferencia entre lo prometido y lo entregado, que es
exactamente lo que el reto pide verificar. Capturarla como texto libre en el
momento de la venta es barato y no cambia el proceso comercial.

**El acta de instalación, adelantada y trazada.** El acta ya existe: la Cláusula
Quinta del contrato obliga al cliente a suscribirla dando conformidad
(`PÚBLICO-WIN`, §3.2). El problema es cuándo llega — hoy se firma *después* de la
instalación, cuando el costo ya se incurrió. No proponemos un artefacto nuevo:
proponemos **adelantar el que ya existe**, convirtiéndolo en una confirmación
breve antes de agendar la visita, y exponer su marca de tiempo como dato.

## 9. Día 1 contra requiere integración

Clasificación por campo, sin preguntas de seguimiento. Es el insumo que la ruta
de adopción consume; la narrativa de adopción no se escribe acá.

**Funciona el día 1, con lo que WIN ya captura (21 campos)**
Todo el bloque A. Habilita: validación de producto, precio, promoción,
combinación producto-zona, condiciones de acceso publicadas, coherencia de la
primera factura, cohorte por asesor y por equipo, y colisión de identidad y
dirección.

**Requiere confirmación, no desarrollo (4 campos)**
Todo el bloque B. Si el registro digital ya los tiene, son día 1 también. Una
conversación lo resuelve.

**Requiere decisión de WIN (5 campos)**
Todo el bloque C. Es lo que habilita verificar la promesa y el consentimiento.
Sin ellos el sistema es un validador de condiciones comerciales; con ellos
responde la pregunta completa del reto.
