# Guía de uso y presentación — WIN · Reto 03

Demo pública: **https://idealistic-carmela-preneolithic.ngrok-free.dev**
Primer acceso desde un teléfono: aparece la página intermedia de ngrok, tocar
**Visit Site**. Nada que instalar, sin credenciales. Todos los datos son
sintéticos.

Láminas: `WIN-Reto03-Pitch-3min.pptx` · Guion hablado: `GUION-PITCH-3MIN.md`.

---

## 1. Dos minutos antes de subir

1. En el portátil, abrir `http://127.0.0.1:8000/salud`. Debe decir `"ok": true`
   y `"llm": "configurada"`. Si `llm` dice otra cosa, la demo igual funciona
   (comparador determinista) y la pantalla lo indica.
2. Abrir la URL pública en tu propio teléfono y tocar **Visit Site**. Dejar la
   pestaña abierta en **Lote**.
3. Abrir el PPT en pantalla completa. Lámina 8 (QR) queda para las preguntas.
4. Un segundo teléfono (compañero o jurado) listo para abrir el enlace de
   confirmación.
5. Portátil enchufado y con la tapa abierta. El servidor y el túnel corren en
   `tmux` (`winapp`, `keepalive`); cerrar la terminal no los apaga.

---

## 2. Mapa del sistema: cinco pantallas

| Pantalla | Ruta | Qué hace | Frase para el jurado |
|---|---|---|---|
| **Nueva venta** | `/` | Formulario móvil de una venta. Botón **Cargar ejemplo** llena una venta limpia. | "Así entra una venta hoy: vendedor, cliente, plan, precio y lo que se prometió en palabras." |
| **Veredicto** | `/ventas/{id}` | Decisión (APROBAR · REVISAR · RETENER · ABSTENERSE), costo esperado en soles, cadena de evidencia, contrafáctico, "Por qué, en palabras", confirmación del cliente. | "No es un score. Es qué no coincide con qué, cuánto cuesta y qué lo arreglaría." |
| **Lote** | `/lote` | Pegar JSON o CSV con cualquier esquema, o botones **Cargar los 25 casos de demo** / **Cargar los 24 casos adversarios**. Reporte de ingesta, Lectura del lote (IA), tabla ordenada por costo recuperable por minuto, matriz de confusión. | "Denos su lote, con sus columnas. Lo mapea, lo separa y muestra cuántos acertó contra sus etiquetas." |
| **Confirmación del cliente** | `/c/{token}` | Lo que ve el cliente en su teléfono: la promesa en lenguaje llano y tres botones. | "El cliente es quien verifica que hay alguien del otro lado. Su silencio también cuenta." |
| **Bandeja** | `/bandeja` | Avisos con destinatario, urgencia, plazo y acción concreta. Botón **Hecho**. | "A quién se le avisa, cuándo, y qué hacer. Ordenado por soles recuperables por minuto." |

---

## 3. Recorrido de demo, paso a paso

### Ruta corta (60 segundos): un lote con esquema ajeno

1. **Lote** → pegar esto (columnas en inglés a propósito, no son las internas):

   ```json
   [
     {"customer": "Ana Quispe",  "phone_number": "912345678", "monthly_price": 99.00, "plan_name": "Fibra 500", "label": "buena"},
     {"customer": "Luis Paredes","phone_number": "923456789", "monthly_price": 40.00, "plan_name": "Fibra 750", "label": "mala"}
   ]
   ```

2. Enviar. Señalar en orden:
   - **Reporte de ingesta**: columnas mapeadas (algunas `mapeado por IA`), no
     reconocidas, faltantes. "No se cae con columnas ajenas."
   - **Lectura del lote**: resumen de la IA con el patrón y la prioridad.
   - **Tabla**: Ana APROBAR, Luis REVISAR (S/ 40 muy por debajo del tarifario
     de Fibra 750).
   - **Matriz de confusión**: contra las etiquetas `buena` / `mala`.
3. Tocar el veredicto de Luis → sección 4 de esta guía.

### Ruta completa (3 a 4 minutos): venta → veredicto → cliente → bandeja

**Paso 1 · Una venta con un defecto (40 s)**

- **Nueva venta** → **Cargar ejemplo** (venta limpia).
- Cambiar dos cosas: precio a `40` y, en "promesa", agregar
  `velocidad garantizada`.
- Enviar. Decir: "Le prometieron algo que el catálogo no sostiene y a un precio
  que no existe."

**Paso 2 · Leer el veredicto (50 s)**

De arriba hacia abajo:

- **Decisión grande** y **costo esperado en soles**. "El corte no se elige a
  dedo: es donde el costo esperado del defecto supera el costo de revisar."
- **Costo por desenlace**: probabilidad × costo de instalación fallida, reclamo,
  baja temprana, reversión de facturación.
- **Cadena de evidencia**: cada regla con la condición y los valores que la
  dispararon, y su **origen** (`PÚBLICO` = tarifario o contrato de WIN;
  `SUPUESTO_DEMO` = supuesto nuestro, declarado). El claim `velocidad
  garantizada` aparece con origen **IA**: la IA lo detectó, la regla decidió.
- **Por qué, en palabras**: redacción de la IA que solo puede citar reglas y
  valores que realmente se dispararon.
- **Contrafáctico**: "si el precio fuera S/ X, esta venta pasaría."

**Paso 3 · El cliente confirma desde otro teléfono (60 s)**

- En el veredicto, bloque **Confirmación del cliente** → **Abrir confirmación**
  (o **Copiar enlace** y mandarlo al segundo teléfono).
- El cliente ve: "Hola {nombre}. {vendedor} te ofreció: {plan} a S/ {precio}/mes.
  ¿Es esto lo que acordaste?" y tres botones: **Sí, es lo que acordé** ·
  **Quiero corregir algo** · **No pedí este servicio**.
- Tocar **No pedí este servicio**. Volver al veredicto: **la decisión cambió**
  (hacia RETENER). "El cliente es el verificador de quién está del otro lado."
- Si sobra tiempo: **Simular vencimiento de ventana (demo)**. "El silencio
  antes de instalar es la señal más fuerte del sistema."

**Paso 4 · La bandeja (30 s)**

- **Bandeja**: cada aviso con destinatario, urgencia, plazo restante y una
  acción ("No despachar. Verificar con el cliente por el enlace"). Tocar
  **Hecho** en uno.

**Paso 5 · El lote (60 s)**

- **Lote** → **Cargar los 24 casos adversarios** (banco del equipo con trampas) o
  **Cargar los 25 casos de demo**. Señalar matriz de confusión y Lectura del
  lote.

### Si el jurado trae su propio lote

- Pegar tal cual en **Lote** (JSON o CSV, cualquier nombre de columna). Si trae
  una columna de etiqueta (`label`, `etiqueta`, `buena/mala`), sale la matriz de
  confusión. Si no, sale la tabla igual.
- Si una fila está rota, el reporte la lista y el resto sigue.
- Positivo = REVISAR o RETENER. ABSTENERSE = no hay evidencia suficiente para
  decidir; se dice explícitamente en vez de adivinar.

---

## 4. Cómo leer un veredicto en voz alta

| Bloque | Qué es | Cómo decirlo |
|---|---|---|
| Decisión | APROBAR / REVISAR / RETENER / ABSTENERSE | "Revisar no es rechazar: es que revisar cuesta menos que dejarla pasar." |
| Costo esperado | Σ probabilidad × costo de cada desenlace | "S/ tanto es lo que esperamos perder si nadie la mira." |
| Cadena de evidencia | Reglas disparadas con condición, valores y origen | "Cada línea dice qué campo no coincide con qué, y de dónde sale el dato." |
| Origen | PÚBLICO · SUPUESTO_DEMO · IA | "Lo público es de WIN; lo supuesto está marcado; la IA solo detecta, no decide." |
| Por qué, en palabras | Explicación en lenguaje llano | "Redactada por la IA, validada contra la evidencia: no puede inventar una regla." |
| Contrafáctico | El cambio mínimo que la haría pasar | "Le dice al vendedor exactamente qué corregir." |
| Confirmación | Estado del cliente: pendiente, confirmó, corrige, rechazó, silencio | "El silencio dentro de la ventana no es un nulo: es una señal." |

---

## 5. Preguntas probables del jurado y respuesta corta

1. **¿Esto es una maqueta?** No. Corre ahora en esa URL; pueden pegar su propio
   lote. 39 reglas, 97 pruebas automáticas, 24 casos adversarios en el repo.
2. **¿De dónde salen los precios y las reglas?** Del tarifario público de WIN
   (win.pe, cartilla informativa, Anexo 1 del contrato) y de OSIPTEL. Lo que
   no es público está marcado `SUPUESTO_DEMO` en pantalla, con su fuente.
3. **¿Y si los datos de WIN tienen otros nombres de columna?** La ingesta mapea
   por nombre aproximado y la IA mapea lo que no reconoce; el reporte lo dice.
   El contrato de datos lista los 30 campos: 21 ya existen, 4 por confirmar,
   5 por capturar.
4. **¿La IA decide?** Nunca. Extrae la promesa, mapea columnas y redacta la
   explicación. La decisión sale del motor de reglas y del costo esperado. Sin
   red, todo sigue funcionando con el comparador determinista.
5. **¿Por qué costo esperado y no un score?** Porque un score no dice cuánto
   vale revisar. Comparar S/ 22,90 de defecto esperado contra S/ 30 de revisión
   es una decisión de negocio que cualquiera puede auditar y ajustar.
6. **¿Cómo tratan al vendedor?** No es vigilancia. Protege al vendedor honesto:
   su venta buena pasa rápido y no carga con el costo del que no lo es. Las
   señales son de la venta, no de la persona.
7. **¿Falsos positivos?** Sobre los 25 casos demo: 0 falsos positivos. El corte
   por costo evita retener ventas buenas: retener también cuesta.
8. **¿Qué necesita WIN para adoptarlo?** Día uno: autónomo con el tarifario
   público. Luego: registro por API, promesa textual y reedición como datos,
   webhooks de despacho/facturación/atención. Piloto de 30 días con Calidad de
   Venta.
9. **¿Qué pasa con la privacidad?** Solo datos sintéticos en la demo. En
   producción el enlace de confirmación lleva un token aleatorio y no expone
   más que la promesa.
10. **¿Qué no sabemos?** Tres cifras: mediana real venta → instalación,
    porcentaje de instalaciones fallidas y costo por minuto del analista. El
    modelo de costo muestra cuánto se mueve el umbral con cada una.

---

## 6. Si algo falla

Orden de repliegue. Nunca detener la demo para recuperar la red.

| Falla | Qué hacer |
|---|---|
| URL pública no abre | Portátil: `http://127.0.0.1:8000`. Proyectar desde el portátil. |
| Servidor caído | En terminal: `tmux new -d -s winapp '.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000'` (el watchdog `keepalive` lo hace solo cada 15 s). |
| Túnel caído | `ngrok http 8000` en otra terminal. La URL cambia: mostrar QR de lámina 8 solo si es la misma. |
| Pantalla dice "IA no disponible: comparador determinista" | Seguir igual. Decir: "sin red la IA degrada y el motor decide igual; la explicación sigue saliendo de las reglas." |
| Lote del jurado no parsea | Pedir CSV o JSON plano. Si insiste, **Cargar los 25 casos de demo** y decir que la ingesta reporta la fila rota y sigue. |
| Segundo teléfono sin red | Abrir el enlace de confirmación en el mismo teléfono o en el portátil. |
| Estado raro (veredictos viejos) | Es estado de demo acumulado; en Bandeja tocar **Hecho** o ignorar. Reinicio limpio: `tmux kill-session -t winapp; unlink data/state.json` y el watchdog relanza. |

---

## 7. Qué decir y qué no decir

- Decir una vez al inicio: "Todos los datos son sintéticos." No volver a
  justificarlo.
- No decir "esto ya está validado con WIN". Decir "con el tarifario público de
  WIN y las cifras de OSIPTEL".
- No prometer cifras de ahorro. Decir "el modelo de costo muestra el umbral y
  qué cifra lo mueve".
- No describir las 39 reglas. Tres bastan: precio fuera de tarifario, promesa
  que el catálogo no sostiene, cliente que no confirma.
- Cerrar siempre con el pedido: piloto de 30 días con Calidad de Venta.
