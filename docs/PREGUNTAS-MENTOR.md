# Banco de preguntas para el mentor comercial

Prometido · Hackatón WIN Chiclayo 2026 · Reto 03 · Fase 0

Estas preguntas están priorizadas: primero las que condicionan el diseño del
motor, después las que ajustan parámetros. Cada una cierra con qué decidimos a
partir de la respuesta. Máximo 12.

---

## 1. Ventana real entre venta e instalación

¿Cuánto tiempo transcurre en la práctica entre que se registra una venta y el
día en que se instala? ¿Varía por canal de venta?

**Qué decidimos con la respuesta:** el valor real de `install_window_hours` y de
`alert_buffer_hours` en `config/settings.yaml`. Hoy asumimos 48 horas de ventana
y 12 horas de margen para avisar; si la realidad es distinta, toda la capa de
aviso se recalibra.

## 2. Cómo queda registrada la promesa hoy

¿En qué campo, nota libre, guion de venta o grabación queda escrito lo que el
vendedor le dijo al cliente? ¿Ese texto se captura de forma estructurada o solo
como nota?

**Qué decidimos con la respuesta:** de dónde sale `promise_text` en producción y
si capturar la promesa es un campo nuevo o un enriquecimiento de algo que ya
existe. Determina si la promesa es un objeto de primera clase viable o un
supuesto.

## 3. Validación de titularidad

¿Cómo se valida hoy que la persona que contrata es el titular de la línea o del
documento? ¿Qué evidencia queda: grabación, firma, SMS, biometría?

**Qué decidimos con la respuesta:** los valores válidos de `consent_evidence` y
si la arista de identidad es una señal fuerte o débil en el registro actual.

## 4. Tasa de instalaciones fallidas por canal

¿Qué proporción de ventas termina en instalación fallida o cancelada, y cuánto
varía entre call center, campo, web y tienda?

**Qué decidimos con la respuesta:** los priors por canal de `config/costs.yaml`
(hoy `SUPUESTO_DEMO`, entre 0.03 y 0.12). Si hay una tasa histórica real, la
señal de cohorte deja de ser supuesto.

## 5. Costo real de cada desenlace

¿Cuánto le cuesta a la operación una instalación fallida, un reclamo, una baja
temprana y una reversión de facturación? ¿Quién absorbe cada costo?

**Qué decidimos con la respuesta:** los valores de `outcomes` y de
`recoverability` en `config/costs.yaml`. Pasamos esos parámetros de supuesto de
demo a dato medido.

## 6. Campos reales del registro de venta

¿Qué campos existen hoy en el sistema de ventas y cómo se llaman exactamente?
¿Cuáles son obligatorios y cuáles quedan vacíos con frecuencia?

**Qué decidimos con la respuesta:** el diccionario de sinónimos de la ingesta y
qué campos del contrato de datos ya existen frente a los que habría que crear.

## 7. A quién le llegan los avisos hoy

¿A quién le llega hoy una venta "rara" y por qué canal? ¿Existe una bandeja de
calidad o se entera despacho recién cuando el técnico está en la puerta?

**Qué decidimos con la respuesta:** los destinatarios y las acciones concretas de
la capa de aviso. El diseño asume dos destinatarios (despacho e instalaciones, y
calidad de venta); confirmamos si son los correctos.

## 8. Cuánto tarda una revisión

¿Cuántos minutos le toma a un analista de calidad revisar una venta y con qué
costo por hora? ¿Es un rol dedicado o lo hace el supervisor?

**Qué decidimos con la respuesta:** `review.cost` y `review.minutes` en
`config/costs.yaml` (hoy S/ 15 y 10 minutos). Es el umbral contra el que se
compara el costo esperado, así que es el parámetro más sensible del modelo.

## 9. Compatibilidad plan–zona

¿Qué tecnologías están disponibles por distrito y qué velocidad máxima soporta
cada zona? ¿Qué distritos no tienen cobertura de fibra?

**Qué decidimos con la respuesta:** la tabla de cobertura de `config/catalog.yaml`
y la arista `registro-entrega` (promesa de una velocidad que la zona no sostiene).

## 10. Promociones y condiciones de combinación

¿Qué promociones existen hoy y a qué planes aplican? ¿Cuáles no son combinables
entre sí?

**Qué decidimos con la respuesta:** `promos.applies_to` y las reglas de
`promesa-catalogo` y `catalogo-registro`. Hoy todo el catálogo es supuesto de
demo; esta respuesta lo convierte en tarifario real.

## 11. Contacto previo a la instalación

¿Existe hoy alguna llamada o mensaje al cliente antes de instalar para confirmar
lo contratado? ¿Quién lo hace y en qué momento?

**Qué decidimos con la respuesta:** si el enlace de confirmación reemplaza un
proceso existente o lo complementa, y quién debería enviarlo.

## 12. Cómo se detecta hoy una venta mala, a posteriori

¿Cómo se entera el área de calidad de que una venta fue mala (reclamo, baja,
nota de crédito)? ¿Con qué retraso y en qué sistema queda registrado?

**Qué decidimos con la respuesta:** cómo se obtienen las etiquetas del arco
(resultado de instalación, primera factura, baja en 90 días) y la latencia del
bucle de aprendizaje del modelo.
