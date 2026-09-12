# Modelo de costo — Reto 03

> **Qué es esto:** el modelo de costo esperado que decide cuándo una venta
> señalada por el rombo de comparadores (promesa · catálogo · registro ·
> entregable) pasa, se revisa o se abstiene. Es la fuente canónica de tres de
> los cinco parámetros compartidos del reto: la ventana de instalación, los
> cuatro desenlaces y el umbral de decisión. `CONTRATO-DE-DATOS.md` y
> `docs/CASOS-ADVERSARIOS.md` los citan por ID; no los redefinen.
>
> **Cómo leer esto:** cada cifra vive una sola vez, en el §3. El resto del
> documento la cita por su ID (`P-NN`); nunca la repite. Las etiquetas de
> origen (`PÚBLICO-WIN`, `PÚBLICO-OSIPTEL`, `TERCERO`, `SUPUESTO`,
> `CONTRADICCIÓN`) siguen la taxonomía de `docs/EVIDENCIA-PUBLICA.md`.

---

## 1. La regla, en una línea

> Un caso pasa a revisión cuando el costo esperado de su defecto supera el
> costo de revisarlo. No es una cifra en soles: es una comparación.

---

## 2. Los cuatro desenlaces

Los cuatro desenlaces son el conjunto canónico de este reto: **instalación
fallida, reclamo, baja temprana, reversión de facturación**. Ningún otro
documento de este reto puede introducir un quinto.

Cada probabilidad de esta tabla es condicional: es la probabilidad de que una
venta **ya señalada** por un desacuerdo entre dos nodos del rombo (promesa
declarada, catálogo vigente, registro de venta, entregable real) derive en ese
desenlace **si nadie la revisa**. No es la probabilidad de que una venta
cualquiera de WIN termine así.

| Desenlace | Probabilidad | Costo unitario | Bloque de origen |
|---|---|---|---|
| Instalación fallida | P-08 | P-09 | Supuesto |
| Baja temprana | P-10 | P-11 (neto de P-05) | Supuesto, neto de un mecanismo Medido |
| Reclamo | P-12 | P-13 | Supuesto |
| Reversión de facturación | P-14 | P-15 (compuesto de P-02 y P-03) | Supuesto, compuesto de dos cargos Medidos |

---

## 3. Registro de parámetros

Toda cifra de este documento aparece una sola vez, acá. El resto del texto
cita el ID.

### Medido

| ID | Parámetro | Valor | `origen:` | Fuente exacta |
|---|---|---|---|---|
| P-01 | Ventana contractual de instalación (techo) | 30 días | `PÚBLICO-WIN` | Anexo 1, "Plazo estimado para la instalación" (preimpreso) — `EVIDENCIA-PUBLICA.md` §4 |
| P-02 | Cargo de instalación | S/120,00 en 6 cuotas de S/20,00 | `PÚBLICO-WIN` | Cartilla informativa §2.2 |
| P-03 | Recargo mensual por recibo físico | S/10,00 por mes | `PÚBLICO-WIN` | Anexo 1, "Forma de entrega del Recibo" — `EVIDENCIA-PUBLICA.md` §4 |
| P-04 | Permanencia forzosa | 6 meses | `PÚBLICO-WIN` | Cartilla §2.5 + Anexo 1 — `EVIDENCIA-PUBLICA.md` §2.5, §4 |
| P-05 | Mecanismo de penalidad por baja anticipada | Devuelve el descuento promocional de los meses ya transcurridos: tarifa oficial vigente al contratar × meses transcurridos − sumas efectivamente pagadas | `PÚBLICO-WIN` | Contrato, Cláusula Cuarta — `EVIDENCIA-PUBLICA.md` §3.1 |
| P-06 | Participación nacional de reclamos de telecom por facturación y cobro, 2025 | 40% (502 944 de 1 257 286) | `PÚBLICO-OSIPTEL` | Informe N° 000069-2025-DAPU/OSIPTEL — `EVIDENCIA-PUBLICA.md` §6.1. Uso: contexto sectorial — no es la probabilidad de reclamo de una venta de WIN (ver P-12) |

### Supuesto

Ninguna cifra de este bloque proviene de datos históricos de WIN: no existe un
historial de incidencia contra el cual calibrarlas. Son valores de trabajo,
explícitos y reemplazables uno por uno. El modelo es abiertamente
paramétrico — no una calibración estadística disfrazada de una.

| ID | Parámetro | Valor de trabajo | Por qué es plausible | Sensibilidad | Pregunta para el mentor (reemplaza este valor) |
|---|---|---|---|---|---|
| P-07 | Mediana real venta → instalación | 10 días | Muy por debajo del techo de 30 días (P-01); el margen documentado en el Anexo 1 es amplio | Si baja mucho, se acorta la ventana operativa de revisión — ver §7 | ¿Cuál es la mediana real de días entre el registro de la venta y la instalación, frente al techo contractual de 30 días? |
| P-08 | Probabilidad de instalación fallida | 5% | Moderada para instalaciones ya agendadas con dirección validada en el formulario | Si sube, acerca el caso al umbral — ver §7 | ¿Qué porcentaje de instalaciones agendadas termina sin instalar por causas no atribuibles a WIN? |
| P-09 | Costo unitario de instalación fallida | S/80,00 | Cubre transporte, tiempo técnico y reprogramación de una visita sin resultado | Mueve el caso al umbral con más fuerza que la probabilidad — ver §7 | ¿Cuánto cuesta hoy una visita técnica que termina sin instalar, incluidos transporte, personal y reprogramación? |
| P-10 | Probabilidad de baja temprana | 6% | Conservadora frente a una permanencia forzosa (P-04) recién comenzada | Si sube, aumenta el costo esperado de este desenlace — ver §7 | ¿Qué porcentaje de ventas con una discrepancia promesa-registro termina en una baja dentro de los 6 meses de permanencia? |
| P-11 | Costo unitario de baja temprana, neto de P-05 | S/95,00 | Margen perdido de los meses restantes después de aplicar la penalidad (P-05), más el retiro del equipo en comodato | Sube si la penalidad recupera poco — ver §7 | Para una baja dentro de la permanencia, ¿cuánto recupera en promedio la penalidad de la Cláusula Cuarta frente al margen perdido, y en qué mes ocurre típicamente? |
| P-12 | Probabilidad de reclamo | 10% | Consistente, de forma conservadora, con el peso nacional de los reclamos de facturación y cobro (P-06) | Si sube, aumenta el costo esperado de este desenlace — ver §7 | ¿Qué porcentaje de ventas con una discrepancia promesa-registro deriva en un reclamo, ante WIN o ante OSIPTEL? |
| P-13 | Costo unitario de reclamo | S/45,00 | Tiempo típico de gestión de un reclamo de facturación en un canal de atención regulado | Sube si el reclamo escala a proceso formal — ver §7 | ¿Cuánto cuesta operativamente atender un reclamo de este tipo, desde el primer contacto hasta su cierre? |
| P-14 | Probabilidad de reversión de facturación | 15% | La cadena de la primera factura (prorrateo + cuota + posible recargo, `EVIDENCIA-PUBLICA.md` §5) hace casi estructural una discrepancia percibida | Es el desenlace más sensible del modelo — ver §7 | ¿Qué porcentaje de ventas con una discrepancia promesa-registro deriva en una reversión formal de facturación? |
| P-15 | Costo unitario de reversión de facturación | S/58,00 | Compuesto por dos cargos ya medidos (1 cuota de instalación, P-02; dos meses de recargo por recibo físico, P-03) más S/18,00 de costo administrativo de emitir la nota de crédito | Sube si el reverso exige más de una nota de crédito — ver §7 | ¿Cuánto cuesta operativamente emitir y conciliar la nota de crédito de una reversión de facturación, sin contar el monto revertido? |
| P-16 | Minutos por caso de revisión manual | 12 minutos | Suficiente para comparar los cuatro nodos del rombo de un caso | Es la variable más frágil del modelo — ver §7 | ¿Cuántos minutos toma en promedio una revisión manual de venta hoy, y qué rol la ejecuta? |
| P-17 | Costo cargado por minuto de revisión | S/2,50 por minuto | Costo cargado típico de un analista de calidad de venta a tiempo parcial | Es la otra variable más frágil del modelo — ver §7 | ¿Cuál es el costo cargado por minuto de ese rol, salario y gastos generales incluidos? |
| P-18 | Volumen diario de ventas, todos los canales | 40 ventas por día | Consistente con una operación multicanal de tamaño medio | No mueve el umbral de un caso individual; mueve cuándo se activa el §6 | ¿Cuál es el volumen diario real de ventas por canal, y cuánta variación estacional tiene? |

---

## 4. Cálculo paso a paso

Caso SIMULADO-MC-01 — sin nombre ni documento de identidad, solo los campos
del Anexo 1 relevantes para este cálculo: el asesor declaró la promesa "sin
permanencia" y "S/79 al mes"; el registro de venta marca `Plazo de vigencia
del contrato: Forzoso (6 meses)` y `Forma de entrega del Recibo: Físico`. Dos
nodos del rombo ya discrepan — el caso entra a este cálculo con una señal
detectada.

1. Instalación fallida: P-08 × P-09 = 5% × S/80,00 = **S/4,00**
2. Baja temprana (neta de P-05): P-10 × P-11 = 6% × S/95,00 = **S/5,70**
3. Reclamo: P-12 × P-13 = 10% × S/45,00 = **S/4,50**
4. Reversión de facturación: P-14 × P-15 = 15% × S/58,00 = **S/8,70**

**Costo esperado total del defecto = S/4,00 + S/5,70 + S/4,50 + S/8,70 = S/22,90**

Cuatro multiplicaciones y una suma, verificables con la calculadora del
teléfono, usando solo los valores impresos en el §3.

---

## 5. El umbral

La regla del §1, con IDs: un caso con evidencia suficiente para estimar su
costo esperado del defecto se compara contra el costo de revisarlo. El
veredicto es uno de tres:

| Veredicto | Cuándo aplica |
|---|---|
| `pasa` | Hay evidencia suficiente para estimar el costo esperado del defecto, y ese costo no supera el costo de revisar |
| `revisar` | Hay evidencia suficiente para estimar el costo esperado del defecto, y ese costo supera el costo de revisar |
| `abstención` | No hay evidencia suficiente para estimar el costo esperado del defecto con confianza — no se calificó como defectuoso, no se pudo calificar (ver §8) |

Aplicado al caso del §4: el costo de revisar este caso es P-16 × P-17 = 12 min
× S/2,50/min = **S/30,00**. Como S/22,90 (costo esperado del defecto) no
supera S/30,00 (costo de revisar), y hay evidencia suficiente para estimarlo,
el veredicto es **`pasa`**.

S/30,00 no es "el umbral": es lo que P-16 × P-17 vale hoy, con los valores de
trabajo vigentes. Si un mentor corrige P-16 o P-17 mañana, la regla del §1
sigue siendo la misma comparación; solo cambia el número que produce.

`abstención` consume el mismo costo de revisión que `revisar` — enruta al
mismo espacio de revisión humana —, pero por una razón distinta: no es que el
caso se haya calificado como caro, es que no se pudo calificar en absoluto.

---

## 6. Cuando no alcanza la capacidad

Cuando el volumen de casos que cruzan el umbral (`revisar` o `abstención`)
supera lo que la capacidad diaria de revisión puede procesar, el orden de
atención se decide por **costo recuperable dividido entre minutos de revisión
consumidos** — nunca por orden de llegada.

```
prioridad = costo esperado recuperable del caso ÷ minutos de revisión que ese caso consume
```

Se asume, para esta primera versión paramétrica, que una revisión a tiempo
evita el desenlace por completo — el costo recuperable es el costo esperado
del defecto calculado en el §4. Si en el futuro se estima que la revisión
solo evita una fracción del desenlace, esa fracción se multiplica en el
numerador; hoy no hay evidencia para estimarla, así que no se inventa.

**Demostración** — valores puramente ilustrativos de dos casos hipotéticos ya
calificados como `revisar`, usados solo para mostrar el mecanismo de orden.
No llevan etiqueta de origen porque no son cifras del modelo ni entran al
registro del §3; no son la tabla de desenlaces con precio del §2/§3/§4:

| Caso | Costo esperado recuperable | Minutos consumidos | Costo recuperable por minuto | Prioridad |
|---|---|---|---|---|
| X | S/40,00 | 12 (P-16) | S/3,33/min | 1 |
| Y | S/35,00 | 25 (caso más complejo) | S/1,40/min | 2 |

Con capacidad para revisar solo uno, la regla prioriza al Caso X en toda
evaluación repetida, usando solamente esta razón — no el tamaño del costo
esperado por sí solo, y no el orden de llegada.

---

## 7. Qué pasa si me equivoqué

Para cada parámetro Supuesto: el valor en el que cambia el veredicto del caso
del §4 — manteniendo los demás parámetros fijos en su valor de trabajo — y si
un rango plausible lo cruza.

| Parámetro | Valor asumido | Valor en que cambia el veredicto | ¿Un rango plausible lo cruza? |
|---|---|---|---|
| P-07 (mediana días) | 10 días | No aplica al costo esperado; aplica a si queda ventana operativa para revisar antes de instalar | No — ninguna fuente sugiere instalación el mismo día; la ventana se mantiene amplia frente a los minutos de revisión (P-16) |
| P-08 (prob. instalación fallida) | 5% | ≈13,9% | Posible en canales o zonas con historial de reagendamiento; no es un valor extremo |
| P-09 (costo instalación fallida) | S/80,00 | ≈S/222,00 | Poco probable como promedio nacional; posible en zonas de logística costosa |
| P-10 (prob. baja temprana) | 6% | ≈13,5% | Cruza solo si la discrepancia promesa-registro es bastante más frecuente que lo asumido |
| P-11 (costo baja temprana) | S/95,00 | ≈S/213,33 | Plausible si la penalidad recupera poco cuando la baja ocurre tarde en los 6 meses |
| P-12 (prob. reclamo) | 10% | ≈25,8% | No se puede descartar — el contexto sectorial (P-06) muestra que los reclamos de facturación no son raros |
| P-13 (costo reclamo) | S/45,00 | ≈S/116,00 | Plausible si el reclamo escala a proceso formal ante OSIPTEL |
| P-14 (prob. reversión de facturación) | 15% | ≈27,2% | Plausible — la cadena de la primera factura hace casi estructural la discrepancia percibida |
| P-15 (costo reversión de facturación) | S/58,00 | ≈S/105,33 | Posible si el reverso exige más de una nota de crédito o más de un área |
| P-16 (minutos por caso) | 12 minutos | ≈9,2 minutos | Sí — un checklist o la precarga de campos del Anexo 1 fácilmente ahorra ese tiempo |
| P-17 (costo por minuto) | S/2,50 | ≈S/1,91 | Sí — un rol de costo cargado menor (analista junior en vez de senior) baja lo suficiente |
| P-18 (volumen diario) | 40 ventas/día | No aplica al veredicto de un caso individual; determina cuándo se activa el §6 | No se puede fijar sin una cifra confirmada de capacidad instalada — pregunta abierta junto con P-16 |

**La prioridad de preguntas al mentor no se afirma, se deriva:** P-16 y P-17
están a apenas ~24% de distancia de su propio punto de cruce. Los cuatro
pares de probabilidad/costo de los desenlaces están entre ~81% (reversión de
facturación) y ~178% (instalación fallida) de distancia del suyo. Con estos
valores de trabajo, el costo de revisar es la parte más frágil del modelo —
no las probabilidades de los desenlaces. Esa es la primera pregunta que vale
la pena llevarle al mentor.

---

## 8. Lo que este modelo todavía no puede estimar

Mientras el catálogo comercial de referencia de WIN no sea uno solo
(`docs/EVIDENCIA-PUBLICA.md` §1), este modelo no tiene contra qué comparar una
promesa para decidir si es correcta o no — y sin esa comparación, no hay
evidencia suficiente para estimar la probabilidad de que el caso derive en
alguno de los cuatro desenlaces. Un caso así no recibe un costo esperado de
defecto: no se calificó como defectuoso, no se pudo calificar. Se resuelve
como **`abstención`** (§5), con el mismo costo que una revisión humana — ni
más barato por no saber, ni más caro por sospechar.

Esta es la única función de esa ambigüedad dentro de este documento: un
costo, no un diagnóstico. Resolverla es una decisión que pertenece al
contrato de datos y al jurado, no a este modelo.
