# Evidencia pública — base documental del Reto 03

> **Qué es esto:** todo dato verificable que tenemos sobre las condiciones
> comerciales de WIN y el mercado peruano, con su fuente exacta. Los tres
> entregables se escriben contra este archivo.
>
> **Regla de uso:** ninguna cifra sale de acá sin su etiqueta de origen. Si no
> está acá, es supuesto y se marca como tal.
>
> **Fecha de recolección:** 2026-09-12.

## Etiquetas de origen

| Etiqueta | Significado |
|---|---|
| `PÚBLICO-WIN` | Documento publicado por WIN en su propio dominio |
| `PÚBLICO-OSIPTEL` | Publicación del regulador |
| `TERCERO` | Comparador, distribuidor o prensa. Citable, pero débil |
| `SUPUESTO` | No existe fuente pública. Solo lo tiene el mentor |
| `CONTRADICCIÓN` | Dos fuentes creíbles dicen cosas distintas |

---

## 1. El hallazgo central

WIN publica **tres catálogos comerciales distintos y mutuamente inconsistentes**
en su propio dominio, y su documento legal obligatorio está desactualizado
respecto de sus páginas de venta.

| Fuente | Escalones de velocidad | Precios | Promoción |
|---|---|---|---|
| Cartilla informativa (documento legal, feb-2024) | 100 · 200 · 300 · 400 · 600 · 1000 Mbps | S/79 – S/259 | No menciona |
| `win.pe/hogar` | 500 · 850 · 1000 Mbps | S/99 – S/179,90 | 1 mes |
| `win.pe/chiclayo` | 350 · 550 · 750 · 1000 Mbps | S/79 – S/159,90 | 3 meses |

**Por qué esto importa más que cualquier otra cosa en este documento:** la
pregunta del reto es cómo verificar que una venta se hizo *con la promesa
correcta*. Validar una promesa exige un catálogo de referencia único. WIN no lo
tiene. Un vendedor puede prometer de buena fe algo de la página de Chiclayo
mientras el contrato que firma el cliente se rige por la cartilla.

**El problema que el reto describe existe, en parte, aguas arriba del vendedor.**
Ese es un replanteo del problema respaldado por documentos de WIN, no una
opinión — y pega directo en los dos criterios de 20%.

*Precaución al presentarlo:* se expone como hallazgo de arquitectura de
información, nunca como señalamiento. El jurado es dueño de esas páginas.

---

## 2. Cartilla informativa — `PÚBLICO-WIN`

Fuente: `https://win.pe/files/cartilla-informativa.pdf?ver=1.2`
Título: "Planes establecidos para el servicio de internet fijo post pago"
Creada: 2024-02-19 · Vigente y publicada al 2026-09-12 · 3 páginas

### 2.1 Tarifario oficial (renta fija mensual, IGV incluido)

| Plan | Renta mensual |
|---|---|
| 100 Mbps *(solo provincias)* | S/79,00 |
| 200 Mbps | S/99,00 |
| 300 Mbps | S/119,00 |
| 400 Mbps | S/129,00 |
| 600 Mbps | S/169,00 |
| 1000 Mbps | S/259,00 |

### 2.2 Instalación

**S/120,00 en 6 cuotas de S/20,00.** Cita: *"Instalación del Servicio — Cuotas: 6
— Cargo: S/120.00 / S/20.00"*.

La investigación previa había concluido que el costo de instalación no estaba
publicado. Sí lo está, en este documento.

### 2.3 Requisitos de acceso — condiciones verificables

> *"Evaluación crediticia favorable (score crediticio mínimo de 201 puntos)"*
> *"No mantener deudas pendientes de pago con WIN u otra empresa por el mismo
> servicio."*

Dos condiciones comerciales explícitas, publicadas y comprobables. Una venta
cerrada con alguien que no las cumple es una venta que no se sostiene. Son
candidatas naturales a regla determinista.

### 2.4 Cobertura

Lima Metropolitana y Callao · Lima provincias: Barranca, Huaral, Hualmay, Huacho
· Provincias: Santa, Trujillo, **Chiclayo**, Lambayeque, Piura.

Chiclayo está en cobertura. El plan de 100 Mbps aplica solo a provincias — es
decir, **la combinación producto/zona ya es una regla de negocio publicada.**

### 2.5 Permanencia — resuelve la contradicción

> *"WIN cuenta con planes forzosos de permanencia de 6 meses."*
> *"Puedes dar por terminado tu contrato de servicio a partir del 7mo mes."*

Literal, en el documento legal de WIN. **Refuta la afirmación «sin permanencia»**
que circula en prensa y comparadores.

### 2.6 Facturación

> *"La facturación de tu servicio es mensual y la modalidad de pago es: mes
> vencido."*
> *"Los días de servicio recibido durante el mes de instalación serán facturados
> (prorrateados) en el mes inmediato siguiente a la activación del servicio."*

Consecuencia directa: **la primera factura nunca es igual al precio mensual
prometido.** Lleva prorrateo del mes de instalación, más la cuota de instalación.
Ver §5.

### 2.7 Velocidad garantizada

70% de la contratada, según normativa. Tabla completa de máxima/mínima por plan,
bajada y subida, en la página 3 de la cartilla.

---

## 3. Contrato de prestación del servicio — `PÚBLICO-WIN`

Fuente: `https://win.pe/files/contrato-internet-fijo-win-pdf-contrato-mtc.pdf`
Contrato estándar MTC de WI-NET TELECOM S.A.C. · 6 páginas, escaneado
*(sin capa de texto; extraído por renderizado y lectura visual)*

### 3.1 Cláusula Cuarta — Plazo y penalidad por baja anticipada

> *"Si el CLIENTE resuelve el contrato antes de su vencimiento o si WIN se ve en
> la necesidad de resolver el contrato por falta de pago o por cualquier otro
> incumplimiento por parte del CLIENTE, éste deberá pagar a WIN como penalidad,
> el total de la retribución (tarifas oficiales vigentes a la fecha de
> celebración del contrato) que hubiera correspondido en caso de haber
> contratado el servicio por el plazo efectivamente transcurrido hasta la
> resolución, menos las sumas efectivamente pagadas."*

**Traducción operativa:** la penalidad es la **devolución del descuento
promocional**. Quien contrató a S/39,50 promocional sobre un plan de S/79 y se
da de baja en el mes 4 debe la diferencia de los meses transcurridos.

Esto es central para el modelo de costo **y** para el reto: al cliente le
prometieron S/39,50 y termina recibiendo una factura de recupero que nadie le
explicó. Es «lo prometido ≠ lo entregado» en su forma más pura, y es
contractual, no un error.

También: vencido el plazo forzoso, el contrato se prorroga automáticamente a
plazo indeterminado **aplicando la tarifa vigente al momento del vencimiento**,
no la contratada. Segundo salto de precio no evidente para el cliente.

### 3.2 Cláusula Quinta — Instalación y acta de conformidad

> *"La instalación del Servicio se efectuará en el plazo consignado en el Anexo 1."*
> *"Efectuada la instalación el CLIENTE deberá suscribir el acta de instalación
> respectiva dando su conformidad."*

**El acta de instalación ya existe.** Es un artefacto de conformidad del cliente
que WIN ya produce hoy. No hay que inventar un mecanismo de confirmación desde
cero: hay que adelantarlo, porque hoy llega *después* de que salió el camión.

Si el cliente no da las facilidades, el cómputo del plazo se suspende.

### 3.3 Otras cláusulas relevantes

- **Décima Primera:** WIN puede suspender el servicio si el cliente se atrasa más
  de **7 días calendario** del vencimiento del recibo.
- **Séptima (q):** el cliente se obliga a observar las normas de secreto de las
  telecomunicaciones y confidencialidad de datos personales. Ancla legal para la
  sección de minimización de datos del contrato de datos.
- **Novena:** mantenimiento incluido en la renta; **reparación se cobra aparte**,
  monto determinado por WIN. Otro vector de factura inesperada.
- Equipos en **comodato**, garantía limitada de 1 año solo por daño de fábrica.

---

## 4. Anexo 1 — el formulario real de registro de venta · `PÚBLICO-WIN`

El Anexo 1 del contrato es **"SOLICITUD DE PRESTACIÓN DEL SERVICIO DE INTERNET A
DOMICILIO"**: el formulario que el asesor llena al cerrar la venta. Es el modelo
de datos verdadero de una venta de WIN. No hay que diseñarlo — hay que leerlo.

### Campos, tal como están impresos

**a) Condiciones técnicas**

| Campo | Valores impresos |
|---|---|
| Velocidad contratada | `30 Mbps ( )` · `100 Mbps ( )` · `.... Mbps ( )` |
| Observaciones | *"El servicio se entrega únicamente en domicilios"* · *"La velocidad garantizada es conforme a la normatividad vigente"* |

**b) Condiciones comerciales**

| Campo | Valor impreso |
|---|---|
| Precio Mensual del Servicio | `S/ ............` |
| **Plazo estimado para la instalación** | **`30 Días`** *(preimpreso)* |
| Forma de pago de instalación | `Primer recibo` |
| Cargos por Servicios de Instalación | `Costo: S/ .......` · `Pago en ( ) cuotas de S/ .......` |
| Forma de pago | `Mes Vencido` |
| **Forma de entrega del Recibo** | **`Físico ( ) Costo S/.10.00 Mensuales`** · `Electrónico ( )` |
| **Plazo de vigencia del contrato** | **`Indeterminado ( )`** · **`Forzoso ( ) 6 meses`** |

**Datos de instalación:** Dirección · Etapa · Nombre del condominio · Torre ·
Departamento

**Datos complementarios del cliente:** **`Propietario ( ) / Inquilino ( )`** ·
Teléfono 1 · Teléfono 2 · Correo electrónico

**Trazabilidad del vendedor:** **`NOMBRE DEL ASESOR`** · **`EQUIPO`**

**Observaciones impresas:**
1. Los montos indicados incluyen el IGV.
2. *"La fecha de alta inicia la facturación del presente servicio y es
   independiente de los valores agregados que provee WIN."*
3. Los equipos instalados se entregan en COMODATO.

**Firma:** EL CLIENTE, con Nombre y documento de identidad.

### Lo que este formulario nos regala

1. **La ventana de instalación es de 30 días, preimpresa.** No de 24 a 72 horas.
   Corrige un supuesto que estaba mal. El margen para intervenir antes del camión
   es enorme — y eso hace que el producto sea *más* viable, no menos. Falta
   preguntarle al mentor cuál es la mediana real frente a ese techo contractual.
2. **`Propietario / Inquilino`** es un campo existente, y es material para
   «quién está del otro lado».
3. **`NOMBRE DEL ASESOR` y `EQUIPO`** ya existen: las señales de cohorte por
   vendedor y por equipo son calculables con datos que WIN ya captura.
4. **`Forzoso 6 meses` es una casilla.** Si el asesor prometió «sin permanencia»
   y marcó `Forzoso`, eso es exactamente un desacuerdo promesa-registro. Sale del
   formulario real.
5. **`Recibo Físico` cuesta S/10 mensuales.** Si el asesor dice «S/79 al mes» y
   marca `Físico`, la factura llega en S/89. Regla no obvia, tomada del
   formulario.
6. **La velocidad se marca con casillas de 30/100 Mbps más un campo libre**, y
   ninguno de esos dos valores existe en el tarifario de la cartilla. El
   formulario y el catálogo tampoco coinciden entre sí.

---

## 5. La primera factura — donde converge todo

Encadenando §2.2, §2.6, §3.1 y §4, la primera factura de un cliente de WIN
contiene, de forma estructural:

1. El prorrateo de los días del mes de instalación *(cartilla §2.6)*.
2. La renta del primer mes completo, mes vencido.
3. La cuota 1 de 6 de instalación, S/20 *(cartilla §2.2)*.
4. S/10 adicionales si se marcó recibo físico *(Anexo 1)*.

**La primera factura no puede ser igual al precio que se prometió.** Nunca.

Contrastar con `PÚBLICO-OSIPTEL` (§6): el **40% de todos los reclamos de
telecomunicaciones del Perú en 2025 fueron por facturación y cobro**.

El enunciado del reto dice: *"antes de que se convierta en una instalación, una
factura y un problema"*. La factura está nombrada en la pregunta. Esta cadena
explica por qué.

---

## 6. OSIPTEL — `PÚBLICO-OSIPTEL`

### 6.1 Reclamos 2025

Fuente: nota de prensa OSIPTEL, *"Cuatro de cada diez reclamos en
telecomunicaciones fueron por facturación y cobro en 2025"* (informe
N° 000069-2025-DAPU/OSIPTEL).

| Métrica | Valor |
|---|---|
| Reclamos totales 2025 | 1 257 286 (+11,56% interanual) |
| **Facturación y cobro** | **502 944 — 40% del total** |
| Internet fijo | 254 437 (+53,14% interanual) |
| Móvil | 751 765 (59,79%, +4,06%) |
| Empaquetados | 130 401 (10,37%) |
| Mes pico | agosto 2025, 124 731 casos |
| Contra 2016 | −43,48% (2,2 M entonces) |

### 6.2 Mercado de internet fijo 2025

Ingresos S/3 751 millones (+5,8%) · más de 4,3 millones de conexiones · fibra
>82% de las conexiones.

### 6.3 Baja del servicio — norma vigente

Resolución 000132-2025-CD/OSIPTEL, vigente desde 2025-06-27:

> *"la empresa operadora debe ejecutar el trámite en el plazo de (1) día hábil de
> solicitada, o en la fecha indicada por el abonado (no menor de un día hábil, ni
> mayor de un mes calendario)"*

Antes eran 5 días hábiles. Además: *"es un derecho del abonado solicitar la baja
de su servicio aun cuando tenga alguna deuda pendiente"*.

**La baja se ejecuta en 1 día hábil. La detección tiene que llegar antes.**

### 6.4 ARPU — no publicado por OSIPTEL · `TERCERO`

La cifra de ~S/69/mes que circula proviene de DN Consultores, no de OSIPTEL.
Ninguna publicación del regulador la contiene. **Para este proyecto es preferible
usar el tarifario propio de WIN (§2.1), que es `PÚBLICO-WIN` y específico.**

---

## 7. Confirmado ausente

| Qué se buscó | Resultado |
|---|---|
| Plazo regulatorio de instalación | **No existe.** La Res. 137-2021-CD/OSIPTEL regula medición de velocidad, no aprovisionamiento. La norma de Condiciones de Uso 2025 fija plazos de migración y baja, no de instalación. El único plazo es contractual: 30 días, Anexo 1 |
| ARPU publicado por OSIPTEL | No encontrado en tres búsquedas |
| Portabilidad de internet fijo | Concepto inaplicable: en Perú la portabilidad es de numeración telefónica |

---

## 8. Contradicciones abiertas — `CONTRADICCIÓN`

1. **Permanencia.** La cartilla y el Anexo 1 de WIN dicen **6 meses forzosos**.
   Prensa y comparadores dicen «sin permanencia». Los documentos propios pesan
   más, pero pueden ser de 2024 y la política pudo cambiar. **Preguntar al
   mentor.** Si efectivamente cambió y la cartilla sigue publicada, eso refuerza
   el hallazgo de §1 en vez de debilitarlo.
2. **Tres catálogos.** Ver §1. Hay que preguntar cuál gobierna Chiclayo.
3. **Velocidades del Anexo 1** (30/100 Mbps) contra el tarifario de la cartilla
   (100–1000 Mbps): el formulario parece más viejo que el catálogo.

---

## 9. Lo que sigue siendo `SUPUESTO`

Ninguna fuente pública los tiene. Son las preguntas al mentor, en orden de
urgencia para el modelo de costo:

1. Mediana real entre venta e instalación, contra el techo contractual de 30 días.
2. Costo de una visita técnica que termina sin falla atribuible a WIN.
3. Costo de una baja dentro de la permanencia, neto del recupero de la penalidad.
4. Minutos y responsable de una revisión manual de venta.
5. Volumen diario de ventas por canal.
6. Si el registro de venta digital tiene más campos que el Anexo 1 impreso.
7. En qué momento se firma hoy el acta de instalación y si queda trazada.

---

## 10. Advertencias de uso

- El dominio **`win-internet.com.pe` no es de WIN**: lleva parámetros de
  afiliado y lo operan distribuidores autorizados. Nunca citarlo como fuente
  propia.
- Los precios de comparadores (Selectra, comparaiso, internet-fibra.pe) son
  `TERCERO`. Tenemos las fuentes propias: usar esas.
- Verificar los precios de las páginas de venta en vivo antes de presentar. Las
  promociones rotan; la cartilla y el contrato no.
- Este proyecto no usa ni reproduce datos personales de ninguna persona real.
  Todos los casos de prueba son sintéticos y van marcados `SIMULADO`.
