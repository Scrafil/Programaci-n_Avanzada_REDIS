# Mi guía — Integrante 1 (C1 + C4 + presentación)

**Mis bloques del video:** presentación (0:00–1:00) + caché **C1** `Avión` 15s
(4:30–5:50) + caché **C4** `Camión` NO_CACHE (5:50–6:50).
**Anexo final:** la condición C3 del Integrante 3, incluida aquí para que entiendas
el proyecto completo (él la presenta; el archivo original sigue en `DB/03_dato_prueba_c3.md`).

Solo necesitas **2 ventanas**: una PowerShell y Postman.

---

## Ventanas y consolas (qué es cada cosa)

- **PowerShell**: la consola azul de Windows. Aquí arrancas la API, Mongo y Redis.
- **Postman**: el programa con el que "consumes" la API (haces peticiones y ves respuestas).
- **WSL/Ubuntu**: NO necesitas abrirlo aparte. Cuando veas un comando que empieza
  con `wsl`, significa "ejecuta esto dentro del Ubuntu"; PowerShell lo reenvía solo.

---

## Paso 0 — Ir a la carpeta del proyecto (PowerShell)

```powershell
cd C:\Users\joans\Downloads\taller_programacion_redis\taller_Redis_Programacion
```

Todo lo de abajo se escribe en esa misma ventana.

## Paso 1 — Encender Redis (PowerShell)

```powershell
wsl sudo service redis-server start
```

Si pide contraseña, es la de tu usuario de Ubuntu. Luego comprueba:

```powershell
wsl redis-cli ping
```

Tienes que ver `PONG`. Eso significa: *"Redis está vivo y escucha"*.
Sin esto, nada de caché funciona.

## Paso 2 — Arrancar la API (PowerShell)

```powershell
python app.py
```

Tienes que ver `Running on http://127.0.0.1:5000`. **Deja esta ventana abierta.**
Si `python` no existe, usa `.\venv\Scripts\python.exe app.py` (hace lo mismo
sin activar el entorno).

> El 404 al abrir `http://127.0.0.1:5000/` en el navegador es normal: la app no
> tiene página principal. Su "¿estás vivo?" es la ruta `/health` (paso 4).

## Paso 3 — Dejar la base limpia (otra PowerShell, en la misma carpeta)

```powershell
mongosh --file DB/01_seed_automoviles.js
```

Al final verás `10` (los 10 vehículos del taller) y los datos del `Avión`.
Luego borra restos de pruebas anteriores en Redis:

```powershell
wsl redis-cli DEL "vehiculo:Avión"
```

Verás `0` o `1`. Ambos valen: *"parto sin caché vieja"*.

## Paso 4 — Importar Postman y probar que todo vive (presentación 0:00–1:00)

1. Abre Postman → botón **Import** → arrastra `postman/taller_vehiculos.json`
   y `postman/entorno_local.json`.
2. Arriba a la derecha elige el entorno **Taller Local**.
3. Abre el request **"00 GET health"** y pulsa **Send**:

```http
GET http://localhost:5000/health
```

Respuesta esperada (código `200`):

```json
{"status": "ok", "mongo": "up", "redis": "up", "db": "automoviles.vehiculos"}
```

**Qué decir (tienes ~1 minuto):** *"API REST en Flask; MongoDB guarda
`automoviles.vehiculos` con 10 vehículos e índice único en `nombre`; Redis en
WSL es el caché. Cada consulta a un vehículo responde el documento más
`fuente` —`mongodb` o `redis`— y `ttl_segundos`. El TTL depende de la longitud
de la **categoría**: hasta 5 caracteres, 15 segundos; 6 a 10, 20 segundos;
11 a 20, 40 segundos; más de 20 no se guarda, con prioridad."*

---

## Paso 5 — C1, primer GET = viene de Mongo (4:30–5:50)

Request **"07 GET Avion 1er"** → **Send**:

```http
GET http://localhost:5000/vehiculos/Avión
```

Respuesta esperada (`200`, tests en verde):

```json
{"nombre": "Avión", "categoria": "Aéreo", "fuente": "mongodb", "ttl_segundos": 15, ...}
```

**Por qué:** es la primera vez que se pide: no está en caché (MISS), la API lo
lee de MongoDB y **lo guarda en Redis por 15 segundos**, porque `"Aéreo"` mide
5 caracteres (`A-é-r-e-o`) y cae en la banda `<= 5`.

## Paso 6 — Mira la clave con tus ojos en Redis

```powershell
wsl redis-cli TTL "vehiculo:Avión"
```

Verás `15`, `14` o `13` (el número baja solo: es la cuenta atrás). Y:

```powershell
wsl redis-cli GET "vehiculo:Avión"
```

Verás el JSON del Avión. **Esto prueba el almacenamiento en caché.**
Di: *"La clave `vehiculo:Avión` existe con TTL 15."*

## Paso 7 — C1, segundo GET = viene de Redis

Request **"08 GET Avion 2do"** → **Send** (el mismo GET de arriba):

```http
GET http://localhost:5000/vehiculos/Avión
```

Respuesta esperada: `"fuente": "redis"` (el `ttl_segundos` será menor de 15:
es lo que **queda**, no lo inicial). **Esto prueba la consulta desde caché.**

## Paso 8 — C1, expiración real en cámara

Espera **16 segundos mirando un cronómetro** y repite el request **07**.
Respuesta esperada: `"fuente": "mongodb"` otra vez.
**Por qué:** los 15 segundos pasaron, Redis borró la clave solo y la API tuvo
que volver a Mongo. Di: *"almacenamiento, consulta y expiración demostrados"*.
Limpieza:

```powershell
wsl redis-cli DEL "vehiculo:Avión"
```

## Paso 9 — C4, primer GET = viene de Mongo y con ttl 0 (5:50–6:50)

Request **"09 GET Camion 1er"** → **Send**:

```http
GET http://localhost:5000/vehiculos/Camión
```

Respuesta esperada: `"fuente": "mongodb", "ttl_segundos": 0`.
**Por qué:** `"Terrestre (motorizado)"` mide 22 caracteres. Supera 20, así que
la regla prioritaria dice **no almacenar**: la API ni siquiera hace `SETEX`.

## Paso 10 — C4, segundo GET = sigue en Mongo + prueba del vacío

Request **"10 GET Camion 2do"** → **Send**: otra vez `"fuente": "mongodb"`.
Y en PowerShell:

```powershell
wsl redis-cli GET "vehiculo:Camión"
```

Verás `(nil)` = *"esa clave jamás existió"*.
Di: *"Dos GET seguidos desde Mongo y nada en Redis: la prioridad funciona."*
**Fin de tu parte.** Sigue el Integrante 2.

---

## Cómo explicar el código (por si te preguntan)

Solo necesitas esta función de `cache.py` (ábrela y muéstrala):

```python
def ttl_para(categoria: str) -> int:
    n = len(categoria or "")   # len = cuántos caracteres mide el texto
    if n > 20:
        return 0               # más de 20 -> 0 = NO guardar (prioritaria)
    if n <= 5:
        return 15              # "Aéreo" mide 5 -> mi caso C1
    if n <= 10:
        return 20
    return 40
```

Explícala así: *"`len` cuenta caracteres. Si la categoría pasa de 20, devuelve 0
y la API no guarda nada; si mide 5 o menos, devuelve 15 y Redis conserva el dato
15 segundos."* El `GET` (`routes/vehiculos_cache.py`) hace esto: busca la clave
`vehiculo:<nombre>` en Redis → si está, responde `fuente: redis`; si no, lee
Mongo, guarda con `SETEX` (guardar **con** tiempo de vida) y responde
`fuente: mongodb`. `TTL` es el tiempo que le queda a una clave; `DEL` la borra
(eso hace el `PUT` del Integrante 2 para no mostrar datos viejos).

## Si algo falla en vivo

- Todo sale `redis` desde el inicio → claves viejas: `wsl redis-cli DEL "vehiculo:Avión"`.
- `/health` dice `redis: down` → repite el paso 1.
- `409` en un POST → ese dato ya existe: normal, sigue con el GET.

---

## Anexo — C3 del Integrante 3 (para que domines el cuadro completo)

**Idea en una frase:** la banda 11–20 caracteres (TTL 40s) no existe en el seed
(las categorías miden 5, 8, 22 o 25), así que el Int. 3 crea **un** documento con
la propia API y demuestra su caché. Esto es lo que él presenta (8:00–9:20):

1. **Crea el dato** (Postman **"16 POST Hidroavion"**):

```http
POST http://localhost:5000/vehiculos
Content-Type: application/json

{"nombre":"Hidroavión","categoria":"Acuático ligero","peso_toneladas":4,"descripcion":"Avión que acuatiza."}
```

Esperado `201`. Por qué 40s: `"Acuático ligero"` mide 15 caracteres (8 + espacio
+ 6… compruébalo: cae entre 11 y 20). Equivalente en mongosh (Parte A del `03`):
`db.vehiculos.insertOne({...})` con ese mismo documento.

2. **MISS:** `GET /vehiculos/Hidroavión` → `"fuente":"mongodb","ttl_segundos":40`.
3. **Redis:** `wsl redis-cli TTL "vehiculo:Hidroavión"` → 38–40.
4. **HIT:** mismo GET → `"fuente":"redis"`.
5. **Expiración (estrategia de video, 40s es largo):** muestra el TTL restante,
   anuncia corte *"tras 40 segundos…"* y muestra el GET final → `"fuente":"mongodb"`.
6. **Limpieza:** `DELETE /vehiculos/Hidroavión` (request 19) y
   `db.vehiculos.countDocuments()` → debe volver a `10`.
