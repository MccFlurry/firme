# Banco de casos adversarios

**24 casos sintéticos diseñados para romper el sistema antes de que lo haga el
jurado.**

El método de juicio del reto es literal: *«que sobre un lote de casos preparado
por el jurado, con ventas buenas y ventas que no lo eran, la propuesta separe
unas de otras y explique en qué se basó»*. Este banco es el ensayo de esa prueba.

Los casos que importan no son los obvios. Son los que una regla ingenua clasifica
mal: la venta correcta que parece sospechosa, y la venta rota que parece limpia.

> **Ningún dato de este documento corresponde a una persona real.** Todos los
> valores de identidad son sintéticos. Los correos usan el dominio reservado
> `.invalid`, que por norma no puede existir. Los asesores son códigos, no
> nombres.

---

## 1. Cómo leer un caso

```
### FAM-NN · SIMULADO · familia: <una de las cuatro> · comparador: <mecánica>

Entrada          Solo los campos que el caso ejercita. Las claves son los
                 nombres exactos de CONTRATO-DE-DATOS.md §4.
Veredicto esperado   pasa · revisar · abstención
Por qué          (1) qué dos nodos del rombo discrepan, citando ambos valores
                 (2) cuál de los cuatro desenlaces se paga si esto pasa
Base             el hecho de política que hace correcto el veredicto, con su
                 etiqueta de origen. Distinta del SIMULADO de los datos
Trampa           qué concluiría de más una regla ingenua. Solo donde aplica
```

El bloque `Entrada` es la **única** copia de los datos del caso: se levanta y se
pega en el prototipo sin retipear. El formato es JSON; la ingesta del prototipo
debe aceptar además CSV y formulario, porque el jurado probablemente traiga sus
casos en una planilla.

Vocabulario de veredicto y umbral: `docs/MODELO-DE-COSTO.md` §5. Los casos límite
citan el umbral en relativo y **nunca** como cifra fija, para que sigan siendo
válidos cuando el mentor entregue los costos reales.

## 2. Índice por comparador

Filas: qué mecánica ejercita el caso. Columnas: las cuatro familias. **Las celdas
vacías son deliberadas y visibles** — son la declaración honesta de lo que este
banco todavía no cubre.

| Mecánica / comparador | Buena | Defectuosa | Ambigua | Límite |
|---|---|---|---|---|
| `CATÁLOGO ↔ REGISTRO` · precio | BUE-01 | DEF-01 | — | LIM-02 |
| `CATÁLOGO ↔ REGISTRO` · velocidad | BUE-04 | DEF-02 | — | LIM-05 |
| `PROMESA ↔ CATÁLOGO` | — | DEF-08 | AMB-03, AMB-05 | — |
| `PROMESA ↔ REGISTRO` · permanencia | — | DEF-03 | — | LIM-01 |
| `PROMESA ↔ REGISTRO` · precio total | BUE-02 | DEF-04 | — | — |
| `REGISTRO ↔ ENTREGABLE` · primera factura | — | — | — | LIM-01 |
| Verificación de titularidad | BUE-03 | DEF-05 | AMB-01, AMB-02, AMB-04 | LIM-04 |
| Colisión de identidad o dirección | — | DEF-06 | AMB-06 | — |
| Condiciones de acceso publicadas | — | DEF-07 | — | — |
| Combinación producto / zona | BUE-04 | — | — | LIM-05 |
| Cohorte por asesor o equipo | BUE-05 | — | — | LIM-03 |

---

## 3. Ventas buenas

Cinco ventas correctas. Tres de ellas están construidas para que una regla
ingenua las marque mal: **un sistema que genera falsos positivos sobre ventas
buenas es peor que no tener sistema**, porque entrena al equipo comercial a
ignorarlo.

### BUE-01 · SIMULADO · familia: buena · comparador: CATÁLOGO ↔ REGISTRO

**Entrada**
```json
{
  "promesa_declarada": "Plan de 200 megas a 99 soles mensuales, instalación en 6 cuotas de 20 soles",
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "cargo_instalacion_costo": 120.00,
  "cargo_instalacion_cuotas": 6,
  "forma_entrega_recibo": "Electronico",
  "plazo_vigencia": "Forzoso_6_meses",
  "direccion": "Av. Simulada 100, Chiclayo",
  "tenencia": "Propietario",
  "telefono_1": "+51 900 000 001",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `pasa`
**Por qué:** (1) Ningún nodo del rombo discrepa: la promesa, el catálogo y el
registro coinciden en velocidad, precio y cargo de instalación. (2) Ninguno de
los cuatro desenlaces tiene por qué activarse.
**Base:** Tarifario 200 Mbps = S/ 99,00 y cargo de instalación S/ 120,00 en 6
cuotas · `PÚBLICO-WIN` · §2.1 y §2.2

### BUE-02 · SIMULADO · familia: buena · comparador: PROMESA ↔ REGISTRO · precio total

**Entrada**
```json
{
  "promesa_declarada": "Plan de 200 megas: 99 soles del plan más 10 soles por recibo físico, total 109 soles al mes",
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "forma_entrega_recibo": "Fisico",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `pasa`
**Por qué:** (1) La promesa declara el total correcto, incluyendo el recargo por
recibo físico. Promesa y entregable coinciden. (2) Ningún desenlace se activa.
**Base:** Recargo por recibo físico S/ 10,00 mensuales · `PÚBLICO-WIN` · §4
**Trampa:** Una regla que marque toda venta con `forma_entrega_recibo: Fisico`
genera un falso positivo acá. El defecto no es el recibo físico: es **no
declararlo en la promesa**. Comparar con DEF-04.

### BUE-03 · SIMULADO · familia: buena · comparador: verificación de titularidad

**Entrada**
```json
{
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "tenencia": "Inquilino",
  "cliente_documento": "SIM-00000003",
  "confirmacion_titular": "confirmada",
  "confirmacion_titular_ts": "2026-09-10T11:20:00-05:00"
}
```
**Veredicto esperado:** `pasa`
**Por qué:** (1) El firmante es inquilino, pero confirmó la venta él mismo y es
quien contrata. No hay discrepancia de identidad. (2) Ningún desenlace se activa.
**Base:** `tenencia` (Propietario / Inquilino) es campo del formulario de venta,
y ser inquilino no es causal de rechazo en ninguna condición publicada ·
`PÚBLICO-WIN` · §4
**Trampa:** Marcar toda venta a inquilinos castiga a un segmento entero por una
condición que WIN no exige. El campo sirve para verificar titularidad, no para
descartar.

### BUE-04 · SIMULADO · familia: buena · comparador: combinación producto / zona

**Entrada**
```json
{
  "promesa_declarada": "Plan de 100 megas a 79 soles",
  "velocidad_contratada": 100,
  "precio_mensual": 79.00,
  "direccion": "Calle Simulada 250, Chiclayo",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `pasa`
**Por qué:** (1) El plan de 100 Mbps existe y aplica en provincias. Chiclayo está
en la lista de cobertura de provincias. Catálogo y registro coinciden. (2) Ningún
desenlace se activa.
**Base:** Plan 100 Mbps = S/ 79,00, marcado *«aplica solo para provincias»*;
Chiclayo figura en la cobertura de provincias · `PÚBLICO-WIN` · §2.1 y §2.4
**Trampa:** Una regla que valide contra el catálogo de Lima marca este caso como
producto inexistente. La combinación producto-zona es una regla publicada, no un
detalle.

### BUE-05 · SIMULADO · familia: buena · comparador: cohorte por asesor

**Entrada**
```json
{
  "velocidad_contratada": 300,
  "precio_mensual": 119.00,
  "nombre_asesor": "ASESOR-014",
  "equipo": "EQUIPO-CHICLAYO-02",
  "forma_entrega_recibo": "Electronico",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `pasa`
**Por qué:** (1) Ningún nodo discrepa. El asesor pertenece a una cohorte con
tasa histórica de defecto elevada, pero esta venta no presenta ninguna
inconsistencia verificable. (2) Ningún desenlace se activa.
**Base:** Tarifario 300 Mbps = S/ 119,00 · `PÚBLICO-WIN` · §2.1
**Trampa:** La cohorte es **calibración previa, no veredicto**. Marcar una venta
impecable por el historial de quien la hizo convierte el sistema en una sanción
individual, y eso es precisamente lo que hace que el área comercial lo rechace.

---

## 4. Ventas defectuosas

Ocho ventas con defecto verificable. Cada una nombra qué dos nodos del rombo
discrepan y con qué valores.

### DEF-01 · SIMULADO · familia: defectuosa · comparador: CATÁLOGO ↔ REGISTRO · precio

**Entrada**
```json
{
  "promesa_declarada": "Plan de 200 megas a 85 soles mensuales",
  "velocidad_contratada": 200,
  "precio_mensual": 85.00,
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) `CATÁLOGO` dice S/ 99,00 para 200 Mbps; `REGISTRO` dice
S/ 85,00. Discrepan en S/ 14,00 mensuales. (2) Reversión de facturación: el
cliente fue facturado a un precio que no existe en el tarifario.
**Base:** Tarifario 200 Mbps = S/ 99,00 · `PÚBLICO-WIN` · §2.1

### DEF-02 · SIMULADO · familia: defectuosa · comparador: CATÁLOGO ↔ REGISTRO · velocidad

**Entrada**
```json
{
  "promesa_declarada": "Plan de 450 megas",
  "velocidad_contratada": 450,
  "precio_mensual": 139.00,
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) `REGISTRO` declara 450 Mbps. Ese escalón no existe en las
condiciones publicadas, que van 100 · 200 · 300 · 400 · 600 · 1000. (2)
Instalación fallida: se aprovisiona un perfil que no corresponde a ningún plan.
**Base:** Escalones de velocidad publicados en la cartilla informativa ·
`PÚBLICO-WIN` · §2.1

### DEF-03 · SIMULADO · familia: defectuosa · comparador: PROMESA ↔ REGISTRO · permanencia

**Entrada**
```json
{
  "promesa_declarada": "Sin permanencia, el cliente se puede ir cuando quiera",
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "plazo_vigencia": "Forzoso_6_meses",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) `PROMESA` dice «sin permanencia»; `REGISTRO` marca la casilla
`Forzoso 6 meses` del mismo formulario que el cliente firmó. Se contradicen en
el mismo papel. (2) Baja temprana con penalidad: el cliente se irá creyendo que
puede, y recibirá un cobro que nadie le anticipó.
**Base:** *«WIN cuenta con planes forzosos de permanencia de 6 meses»* y *«Puedes
dar por terminado tu contrato de servicio a partir del 7mo mes»* ·
`PÚBLICO-WIN` · §2.5
**Trampa:** La afirmación «WIN es sin permanencia» circula en prensa y
comparadores. Un sistema que la tome como verdad valida este caso como correcto.
La fuente que gobierna es el documento propio de WIN, no la nota de prensa.

### DEF-04 · SIMULADO · familia: defectuosa · comparador: PROMESA ↔ REGISTRO · precio total

**Entrada**
```json
{
  "promesa_declarada": "99 soles al mes, todo incluido",
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "forma_entrega_recibo": "Fisico",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) `PROMESA` dice S/ 99,00 «todo incluido»; el `ENTREGABLE` será
S/ 109,00, porque el recibo físico agrega S/ 10,00 mensuales. (2) Reclamo y
reversión de facturación: la primera factura no coincidirá con lo prometido.
**Base:** *«Forma de la entrega del Recibo: Físico ( ) Costo S/.10.00
Mensuales»*, campo del formulario de venta · `PÚBLICO-WIN` · §4
**Trampa:** El registro es internamente consistente y el precio del plan es
correcto. Un validador que solo compare `precio_mensual` contra el tarifario
aprueba esta venta. El defecto está entre la promesa y el total.

### DEF-05 · SIMULADO · familia: defectuosa · comparador: verificación de titularidad

**Entrada**
```json
{
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "cliente_documento": "SIM-00000005",
  "telefono_1": "+51 900 000 005",
  "confirmacion_titular": "negada",
  "confirmacion_titular_ts": "2026-09-11T09:05:00-05:00"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) El titular declarado niega haber contratado. `REGISTRO` afirma
una venta que el `ENTREGABLE` no tiene a quién entregarle. (2) Los cuatro
desenlaces a la vez: instalación fallida, reclamo, baja inmediata y reversión.
Es el caso más caro del banco.
**Base:** `confirmacion_titular` es el campo de consentimiento definido en
`CONTRATO-DE-DATOS.md` §6; el estado `negada` es el más grave de su enumeración ·
`SUPUESTO` (campo propuesto, no existe hoy) · §9 punto 7

### DEF-06 · SIMULADO · familia: defectuosa · comparador: colisión de identidad

**Entrada**
```json
{
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "cliente_documento": "SIM-00000006",
  "telefono_1": "+51 900 000 001",
  "direccion": "Jr. Simulado 410, Chiclayo",
  "nombre_asesor": "ASESOR-027",
  "confirmacion_titular": "enviada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) `telefono_1` coincide con el de BUE-01, que corresponde a otro
documento de cliente y otra dirección. Dos titulares distintos no comparten
teléfono de contacto. (2) Instalación fallida y reclamo: la confirmación llegará
a una persona que no es el titular de esta venta.
**Base:** `telefono_1` y `cliente_documento` son campos del formulario de venta ·
`PÚBLICO-WIN` · §4

### DEF-07 · SIMULADO · familia: defectuosa · comparador: condiciones de acceso publicadas

**Entrada**
```json
{
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "score_crediticio": 178,
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) El score declarado está por debajo del mínimo publicado de 201
puntos. La venta no cumple una condición de acceso que WIN publica. (2) Baja
temprana y reversión: una venta que no debió cerrarse termina en morosidad y
suspensión.
**Base:** *«Evaluación crediticia favorable (score crediticio mínimo de 201
puntos)»* · `PÚBLICO-WIN` · §2.3
**Trampa:** Depende de `score_crediticio`, campo del bloque B marcado
*confirmar*. Si WIN no lo expone al registro de venta, este chequeo no corre y
el caso degrada a `pasa` sin esa verificación. Ver `CONTRATO-DE-DATOS.md` §4.

### DEF-08 · SIMULADO · familia: defectuosa · comparador: PROMESA ↔ CATÁLOGO

**Entrada**
```json
{
  "promesa_declarada": "Plan de 400 megas con dos routers mesh incluidos sin costo",
  "velocidad_contratada": 400,
  "precio_mensual": 129.00,
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) `PROMESA` ofrece dos equipos mesh incluidos; el `CATÁLOGO` los
declara *«a solicitud»*, no incluidos por derecho. El plan y el precio son
correctos: lo que no existe es el beneficio prometido. (2) Reclamo: el cliente
reclamará un equipo que nadie se comprometió formalmente a entregarle.
**Base:** Equipos mesh publicados como *«a solicitud»*, 1 o 2 unidades según
plan, sin precio declarado · `PÚBLICO-WIN` · §1
**Trampa:** Sin el campo `promesa_declarada` este defecto es invisible. El
registro es impecable. Es el caso que justifica capturar la promesa como dato.

---

## 5. Casos ambiguos

Seis casos con evidencia en ambas direcciones. Ejercitan el derecho a
abstenerse: **un sistema que nunca dice «no tengo con qué decidir» no es
confiable, solo es seguro de sí mismo.**

### AMB-01 · SIMULADO · familia: ambigua · comparador: verificación de titularidad

**Entrada**
```json
{
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "telefono_1": "+51 900 000 011",
  "confirmacion_titular": "no_respondida",
  "confirmacion_titular_ts": null
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) No hay discrepancia entre nodos: todo lo verificable coincide.
Lo que falta es la confirmación del titular, y la ventana venció. El silencio no
prueba que la venta sea falsa, pero es la señal más fuerte disponible. (2) Baja
temprana y reclamo, ponderados por la probabilidad de que el silencio indique un
titular que no reconoce la venta.
**Base:** `no_respondida` es un estado explícito de `confirmacion_titular`, no un
valor nulo; la distinción está definida en `CONTRATO-DE-DATOS.md` §6 ·
`SUPUESTO` (campo propuesto) · §9 punto 7
**Trampa:** Tratar el silencio como campo vacío lo vuelve indistinguible de una
confirmación que nunca se envió. Son dos situaciones opuestas.

### AMB-02 · SIMULADO · familia: ambigua · comparador: verificación de titularidad

**Entrada**
```json
{
  "promesa_declarada": "Plan de 300 megas a 119 soles",
  "velocidad_contratada": 300,
  "precio_mensual": 119.00,
  "confirmacion_titular": "confirmada_con_correccion",
  "confirmacion_titular_ts": "2026-09-11T18:40:00-05:00"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) El cliente reconoce la venta, de modo que la identidad está
verificada, pero corrige lo prometido: dice que le ofrecieron 400 Mbps. `PROMESA`
según el asesor y `PROMESA` según el cliente no coinciden. (2) Reclamo: el
cliente esperará un producto distinto del que se le va a instalar.
**Base:** `confirmada_con_correccion` es un estado propio de
`confirmacion_titular`, distinto de `confirmada` y de `negada` ·
`SUPUESTO` (campo propuesto) · §9 punto 7
**Trampa:** Colapsar este estado en `confirmada` pierde exactamente la
información que el mecanismo existe para capturar. La corrección **es** el dato.

### AMB-03 · SIMULADO · familia: ambigua · comparador: PROMESA ↔ CATÁLOGO

**Entrada**
```json
{
  "promesa_declarada": "Plan de 850 megas a 119 soles",
  "velocidad_contratada": 850,
  "precio_mensual": 119.00,
  "catalogo_referencia_id": null,
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `abstención`
**Por qué:** (1) El escalón de 850 Mbps aparece en una de las superficies
comerciales publicadas, pero no en las condiciones informativas, que van 100 ·
200 · … · 1000. Sin un catálogo de referencia versionado no se puede determinar
cuál gobernaba al momento de la venta, y por lo tanto **no se puede afirmar que
la promesa sea incorrecta**. (2) Ninguno: el costo de este caso es el de una
revisión, no el de un defecto.
**Base:** Las condiciones publicadas y las superficies de venta describen
escalones distintos · `CONTRADICCIÓN` · §1 y §8
**Trampa:** Marcarlo como defecto acusa al asesor de algo que puede haber hecho
bien. El campo `catalogo_referencia_id` es nulo: el sistema no tiene contra qué
contrastar y lo dice. Ver `docs/MODELO-DE-COSTO.md` §8.

### AMB-04 · SIMULADO · familia: ambigua · comparador: verificación de titularidad

**Entrada**
```json
{
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "tenencia": "Inquilino",
  "cliente_documento": "SIM-00000014",
  "telefono_1": "+51 900 000 014",
  "confirmacion_titular": "confirmada",
  "confirmacion_titular_ts": "2026-09-11T12:00:00-05:00"
}
```
**Veredicto esperado:** `abstención`
**Por qué:** (1) La confirmación llegó y es afirmativa, pero se envió al teléfono
registrado, y no hay evidencia de que ese número corresponda al firmante y no a
un tercero del domicilio. Confirmar no es lo mismo que confirmar **el titular**.
(2) Ninguno cuantificable: el sistema no puede estimar la probabilidad sin saber
a quién llegó la confirmación.
**Base:** `tenencia` y `telefono_1` son campos del formulario; ninguna condición
publicada vincula el teléfono de contacto con la identidad del firmante ·
`PÚBLICO-WIN` · §4

### AMB-05 · SIMULADO · familia: ambigua · comparador: PROMESA ↔ CATÁLOGO

**Entrada**
```json
{
  "promesa_declarada": "Precio promocional por seis meses y después sube",
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "catalogo_referencia_id": null,
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `abstención`
**Por qué:** (1) La promesa declara una duración promocional de seis meses. Las
superficies comerciales publicadas declaran duraciones distintas entre sí, y las
condiciones informativas no declaran ninguna. No hay contra qué validar. (2)
Ninguno cuantificable, por la misma razón que AMB-03.
**Base:** Duraciones promocionales divergentes entre superficies publicadas ·
`CONTRADICCIÓN` · §1

### AMB-06 · SIMULADO · familia: ambigua · comparador: colisión de dirección

**Entrada**
```json
{
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "direccion": "Av. Simulada 900, Chiclayo",
  "nombre_condominio": "Condominio Simulado",
  "torre": null,
  "departamento": null,
  "cliente_documento": "SIM-00000016",
  "confirmacion_titular": "enviada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) Es la tercera venta del día a la misma dirección normalizada.
Puede ser un condominio real con varias altas legítimas, o ventas duplicadas
sobre un mismo punto. `torre` y `departamento` están vacíos, y son los campos que
lo distinguirían. (2) Instalación fallida: el técnico no sabrá a qué unidad ir.
**Base:** `nombre_condominio`, `torre` y `departamento` son campos del formulario
de venta, opcionales · `PÚBLICO-WIN` · §4
**Trampa:** Marcar toda dirección repetida penaliza los condominios, donde varias
altas el mismo día son normales. Lo que discrimina es la **ausencia de torre y
departamento**, no la repetición.

---

## 6. Casos límite

Cinco casos cerca de una frontera. Todos describen su posición **en relativo al
umbral**, nunca con una cifra fija en soles.

### LIM-01 · SIMULADO · familia: límite · comparador: REGISTRO ↔ ENTREGABLE · primera factura

**Entrada**
```json
{
  "promesa_declarada": "39.50 al mes por el plan de 100 megas",
  "velocidad_contratada": 100,
  "precio_mensual": 39.50,
  "plazo_vigencia": "Forzoso_6_meses",
  "cargo_instalacion_costo": 120.00,
  "cargo_instalacion_cuotas": 6,
  "forma_pago": "Mes_Vencido",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) El precio promocional es real y está publicado, así que
`CATÁLOGO ↔ REGISTRO` coincide. La discrepancia es con el `ENTREGABLE`: la
primera factura llevará prorrateo del mes de instalación, la renta del primer mes
y la primera de seis cuotas de instalación. Y si el cliente se da de baja dentro
del período forzoso, la penalidad contractual le devuelve el descuento
promocional acumulado. Nada de eso está en la promesa. (2) Reclamo y reversión de
facturación en el primer ciclo; baja temprana con penalidad después.
**Base:** Facturación mes vencido con prorrateo del mes de instalación (§2.6);
cargo de instalación en 6 cuotas (§2.2); penalidad de resolución anticipada de la
Cláusula Cuarta, que cobra la tarifa oficial del período transcurrido menos lo
efectivamente pagado (§3.1) · `PÚBLICO-WIN`
**Trampa:** Es el caso más difícil del banco y el más frecuente en la realidad.
Todo está correctamente registrado, el precio existe, el cliente confirmó, y el
asesor no mintió. **El defecto es estructural: la primera factura de WIN nunca
puede ser igual al precio mensual prometido.** Un sistema que solo compare
registro contra catálogo aprueba este caso, y este caso es la razón por la que el
40 % de los reclamos del país son de facturación y cobro (`PÚBLICO-OSIPTEL`, §6.1).

### LIM-02 · SIMULADO · familia: límite · comparador: CATÁLOGO ↔ REGISTRO · precio

**Entrada**
```json
{
  "promesa_declarada": "Plan de 400 megas a 129 soles",
  "velocidad_contratada": 400,
  "precio_mensual": 129.00,
  "forma_entrega_recibo": "Electronico",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `pasa`
**Por qué:** (1) El precio es exactamente el publicado para ese plan. Coincidencia
exacta, sin margen ni redondeo. (2) Ninguno. El costo esperado queda **por debajo
del umbral**.
**Base:** Tarifario 400 Mbps = S/ 129,00 · `PÚBLICO-WIN` · §2.1
**Trampa:** Existe para verificar lo contrario de DEF-01: que el sistema no marca
por proximidad. Un precio correcto no debe generar ruido solo por estar cerca de
uno incorrecto.

### LIM-03 · SIMULADO · familia: límite · comparador: cohorte por asesor

**Entrada**
```json
{
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "nombre_asesor": "ASESOR-014",
  "equipo": "EQUIPO-CHICLAYO-02",
  "telefono_2": null,
  "correo_electronico": null,
  "forma_entrega_recibo": "Electronico",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `pasa`
**Por qué:** (1) Ningún nodo discrepa. Faltan dos campos opcionales —contacto
alterno y correo— que apagan señales secundarias sin afectar ningún comparador.
(2) El costo esperado queda **apenas por debajo del umbral**: la cohorte lo
empuja hacia arriba, la ausencia de discrepancias lo mantiene abajo.
**Base:** `telefono_2` y `correo_electronico` son campos opcionales del
formulario · `PÚBLICO-WIN` · §4
**Trampa:** Es el caso que se mueve primero cuando el mentor entregue costos
reales. Si la revisión resulta más barata de lo supuesto, este caso cruza a
`revisar`. Por eso no lleva cifra: sigue siendo válido con cualquier umbral.

### LIM-04 · SIMULADO · familia: límite · comparador: verificación de titularidad

**Entrada**
```json
{
  "velocidad_contratada": 200,
  "precio_mensual": 99.00,
  "plazo_estimado_instalacion": 30,
  "confirmacion_titular": "confirmada",
  "confirmacion_titular_ts": "2026-09-12T08:15:00-05:00"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) La confirmación es afirmativa, pero llegó después de vencida la
ventana de verificación. La identidad quedó verificada tarde: la instalación ya
estaba agendada. No hay discrepancia de contenido, sí de oportunidad. (2)
Instalación fallida, si la confirmación tardía hubiera traído una corrección.
**Base:** La ventana contractual de instalación es `P-01`, y la ventana de
verificación es `P-07`, acotada por ella · `PÚBLICO-WIN` y `SUPUESTO` · §4 y §9
punto 1
**Trampa:** Un sistema que solo mire el estado final ve `confirmada` y aprueba.
Lo que importa es **cuándo** llegó respecto de la ventana, no solo qué dijo.

### LIM-05 · SIMULADO · familia: límite · comparador: combinación producto / zona

**Entrada**
```json
{
  "promesa_declarada": "Plan de 100 megas a 79 soles",
  "velocidad_contratada": 100,
  "precio_mensual": 79.00,
  "direccion": "Av. Simulada 55, Lima",
  "confirmacion_titular": "confirmada"
}
```
**Veredicto esperado:** `revisar`
**Por qué:** (1) El plan y el precio son correctos, pero el catálogo restringe el
escalón de 100 Mbps a provincias, y la dirección es de Lima. `CATÁLOGO ↔
REGISTRO` discrepa en la dimensión de zona, no en la de precio. (2) Instalación
fallida: se vende un perfil que no aplica en esa plaza.
**Base:** *«El plan de 100 Mbps aplica solo para provincias»* · `PÚBLICO-WIN` ·
§2.1
**Trampa:** Es el mismo plan y el mismo precio que BUE-04, que sí pasa. Lo único
que cambia es la zona. Un validador que ignore la dimensión geográfica no puede
distinguir estos dos casos, y son opuestos.

---

## 7. Lo que este banco todavía no cubre

Las celdas vacías de la matriz de la §2 son deliberadas. Esto es lo que falta y
por qué.

**Depende de qué señales implemente el prototipo.** Estas familias están
descritas en el prompt maestro pero el equipo aún no seleccionó cuáles se
construyen en vivo. No se escriben casos que dependan de ellas, porque un caso
que el prototipo no puede ejecutar no sirve para demostrar nada:

- Ráfaga de ventas del mismo asesor en pocos minutos.
- Tiempo de llenado del formulario anormalmente corto.
- Registro de venta fuera del patrón horario.
- Señal de reedición: cuántas veces se corrigió el registro y qué campo se tocó.

Las dos últimas dependen además de `fecha_hora_registro` y `ediciones_registro`,
campos del bloque B marcados *confirmar* en `CONTRATO-DE-DATOS.md` §4.

**Depende de respuestas del mentor.** Los casos límite están posicionados
relativamente al umbral, no en soles. Cuando lleguen los costos reales, LIM-03 es
el primero que puede cambiar de lado. Ningún caso necesita reescritura por eso:
ninguno lleva una cifra de umbral.

**Falta cobertura de `REGISTRO ↔ ENTREGABLE` fuera de la primera factura.** Hoy
solo LIM-01 ejercita ese comparador. Los casos de instalación —lo que se instaló
contra lo que se registró— requieren `acta_instalacion_ts`, que es un campo
propuesto y no existe hoy.

---

## 8. Alcance

Ningún caso de este banco propone modificar un precio, una comisión ni un
esquema de incentivos. Eso está fuera del campo del reto
(`RETO-03-FUENTE.md` §5).

Los 24 casos son sintéticos y están marcados `SIMULADO`. Los hechos de política
sobre los que se construyen llevan su propia etiqueta de origen, distinta de esa
marca, y son verificables en `docs/EVIDENCIA-PUBLICA.md`.
