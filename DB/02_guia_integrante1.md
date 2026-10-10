# Mi guía — Integrante 1 (C1 + C4 + presentación)

**Mis bloques del video:** presentación (0:00–1:00) + caché **C1** `Avión` 15s
(4:30–5:50) + caché **C4** `Taxi` NO_CACHE (5:50–6:50).
Solo necesitas: app **Ubuntu**, una PowerShell, Postman y Compass.

---

## 0. Cómo funciona el proyecto (para explicarlo en 1 minuto)

Archivos importantes y cómo se hablan entre ellos:

```text
Postman (tú pides) ──HTTP──▶ app.py (puerta Flask)
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
          config.py    routes/vehiculos.py   routes/vehiculos_cache.py
          (lee .env:   (POST/GET lista/      (GET /vehiculos/<nombre>:
           direcciones  PUT/DELETE)           pregunta a cache.py)
           de Mongo y
           Redis)               │               │
                                ▼               ▼
                          MongoDB:          Redis (WSL):
                          automoviles.      clave vehiculo:<nombre>
                          vehiculos         con tiempo de vida
                          (datos reales)    (copia rápida)
```

- **`app.py`**: arranca el servidor y declara las rutas. No guarda nada.
- **`config.py`**: lee el `.env` (direcciones de Mongo y Redis).
- **`routes/vehiculos.py`**: crea, lista, actualiza y borra (CRUD contra Mongo).
- **`routes/vehiculos_cache.py` + `cache.py`**: al pedir UN vehículo, miran Redis
  primero (`fuente: redis`); si no está, leen Mongo, lo guardan con `SETEX`
  (guardar **con** segundos de vida) y responden `fuente: mongodb`.
- **`cache.py → ttl_para`**: decide los segundos según `len(categoria)`:
  `<=5`→15, `6-10`→20, `11-20`→40, `>20`→0 (no guardar, prioritaria).

## 1. Qué rutas existen y para qué sirve cada una

Base: `http://localhost:5000` (en tu PC también vale `http://127.0.0.1:5000`).

| Método + ruta | Para qué sirve |
|---|---|
| `GET /health` | "¿Estás vivo?" Responde `{"status":"ok","mongo":"up","redis":"up","db":"automoviles.vehiculos"}`: `mongo`/`redis` dicen si cada servicio responde; `db` dice qué base y colección se usa. (El 404 de `/` es normal: no hay página principal.) |
| `GET /vehiculos` | Lista todos (la usa el Int. 3). |
| `GET /vehiculos/<nombre>` | **Tus demos.** Devuelve el documento + `fuente` (`mongodb` = lo leyó de la base; `redis` = lo leyó del caché) + `ttl_segundos` (banda que le tocó; en HIT es lo que **queda**). |
| `POST /vehiculos` | **Tu demo C4.** Crea con body JSON (los 4 campos). Responde `201` (o `409` si el nombre ya existe). |
| `PUT` / `DELETE /vehiculos/<nombre>` | Las usa el Int. 2 (actualizar/borrar + invalidar caché). |

## 2. Dos ejemplos directos de `taller_vehiculos.json` (así los verás)

**Ejemplo 1 — petición GET (así pides el Avión):**

```http
GET http://localhost:5000/vehiculos/Avión
```

Sin body. La respuesta trae el documento más `"fuente"` y `"ttl_segundos"`.
En la colección este es el request **"07 GET Avion 1er"**, que además trae tests
que comprueban solos `fuente == "mongodb"` y `ttl_segundos == 15`.

**Ejemplo 2 — petición POST (así se crea un vehículo):**

```http
POST http://localhost:5000/vehiculos
Content-Type: application/json

{"nombre": "PruebaCRUD", "categoria": "Aéreo", "peso_toneladas": 1, "descripcion": "Prueba CRUD."}
```

Pestaña **Body** → **raw** → **JSON**, pegas eso y **Send** → esperado `201`.
En la colección es el request **"02 CRUD POST PruebaCRUD"**.

---

## 3. Arranque (hazlo una vez)

En la app **Ubuntu**:

```bash
sudo service redis-server start
redis-cli ping            # -> PONG (Redis vivo)
```

En PowerShell (carpeta del proyecto):

```powershell
cd C:\Users\joans\Downloads\taller_programacion_redis\taller_Redis_Programacion
python app.py             # -> Running on http://127.0.0.1:5000 (dejar abierto)
```

En otra PowerShell (misma carpeta), seed limpio + sin caché vieja:

```powershell
mongosh --file DB/01_seed_automoviles.js   # -> al final: 10
```

En Ubuntu:

```bash
redis-cli DEL "vehiculo:Avión" "vehiculo:Taxi"   # -> 0, 1 o 2: parto limpio
```

En Postman: **Import** → `postman/taller_vehiculos.json` + `entorno_local.json`
→ entorno **Taller Local**. En Compass (opcional): conecta a
`mongodb://localhost:27017` → `automoviles` → `vehiculos` (10 documents).

## 4. Presentación (0:00–1:00): `GET /health`

Request **"00 GET health"** → **Send** → `200`:

```json
{"status": "ok", "mongo": "up", "redis": "up", "db": "automoviles.vehiculos"}
```

Di: *"Flask expone la API; MongoDB guarda 10 vehículos con índice único en
`nombre`; Redis en WSL es el caché. Cada consulta responde `fuente` y
`ttl_segundos`, y el TTL depende de la longitud de la categoría: hasta 5 son 15
segundos; más de 20 no se guarda, con prioridad."*

## 5. Demo C1 con GET — `Avión`, 15s (4:30–5:50)

`"Aéreo"` mide 5 caracteres → banda `<= 5` → TTL 15.

1. Request **"07 GET Avion 1er"** → **Send**:
   `GET http://localhost:5000/vehiculos/Avión` → `200`
   `{"fuente":"mongodb","ttl_segundos":15,...}`.
   Di: *"Primer GET: MISS, viene de Mongo y se guarda en Redis."*
2. Ubuntu: `redis-cli TTL "vehiculo:Avión"` → verás `15/14/13` (cuenta atrás).
   `redis-cli GET "vehiculo:Avión"` → el JSON. Di: *"Almacenamiento demostrado."*
3. Request **"08 GET Avion 2do"** → **Send** → `"fuente":"redis"`.
   Di: *"Segundo GET: HIT, consulta desde caché."*
4. Espera **16s** (cronómetro) → repite **07** → `"fuente":"mongodb"`.
   Di: *"Expiró y volvió a Mongo: expiración automática demostrada."*
5. Limpia: `redis-cli DEL "vehiculo:Avión"`.

## 6. Demo C4 con POST + GET — `Taxi`, no se guarda (5:50–6:50)

`"Terrestre (motorizado)"` mide 22 caracteres → supera 20 → **nunca se guarda**.

1. Crea el dato (petición manual, pestaña Body → raw → JSON):

```http
POST http://localhost:5000/vehiculos
Content-Type: application/json

{"nombre": "Taxi", "categoria": "Terrestre (motorizado)", "peso_toneladas": 1.4, "descripcion": "Taxi amarillo."}
```

Esperado `201`. Di: *"Creo un vehículo cuya categoría mide 22."*

2. `GET http://localhost:5000/vehiculos/Taxi` → `200`
   `{"fuente":"mongodb","ttl_segundos":0,...}`.
3. Repite el GET → otra vez `"fuente":"mongodb"`.
4. Ubuntu: `redis-cli GET "vehiculo:Taxi"` → `(nil)` = *"esa clave jamás existió"*.
   Di: *"Dos GET desde Mongo y nada en Redis: la regla prioritaria funciona
   también con datos nuevos, no solo con el seed."*
5. Limpieza obligatoria: `DELETE http://localhost:5000/vehiculos/Taxi` → `200`,
   y `db.vehiculos.countDocuments()` → `10`. Sigue el Int. 2.

## 7. Código que puedo explicar (si preguntan)

Muestra `cache.py`:

```python
def ttl_para(categoria: str) -> int:
    n = len(categoria or "")   # len = cuántos caracteres mide
    if n > 20:
        return 0               # >20 -> 0 = NO guardar (mi caso C4: 22)
    if n <= 5:
        return 15              # "Aéreo" = 5 -> mi caso C1
    if n <= 10:
        return 20
    return 40
```

Di: *"`len` cuenta caracteres. `Taxi` es categoría de 22: retorna 0 y la API
jamás hace `SETEX`; `Avión` es de 5: retorna 15 y Redis lo conserva 15
segundos."* `TTL` = lo que le queda a una clave; `DEL` = borrarla.

## 8. Si falla en vivo

- Todo sale `redis` al empezar → `redis-cli DEL "vehiculo:Avión" "vehiculo:Taxi"`.
- `redis: down` → `sudo service redis-server start` en Ubuntu.
- `409` en el POST del Taxi → ya existe de un ensayo: bórralo con el `DELETE` y repite.

---

## Anexo — C3 del Integrante 3 (lo presenta él; aquí para tu dominio total)

La banda 11–20 (TTL 40s) no existe en el seed (categorías de 5, 8, 22, 25).
El Int. 3 crea **un** documento vía POST y demuestra su caché
(detalle: `DB/03_dato_prueba_c3.md`):

```http
POST http://localhost:5000/vehiculos
Content-Type: application/json

{"nombre":"Hidroavión","categoria":"Acuático ligero","peso_toneladas":4,"descripcion":"Avión que acuatiza."}
```

`"Acuático ligero"` = 15 caracteres → TTL 40. Luego:
`GET /vehiculos/Hidroavión` → `mongodb`/40 → `redis-cli TTL` (38–40) →
mismo GET → `redis` → (esperar 41s) → `mongodb` → `DELETE` (vuelve a 10).
