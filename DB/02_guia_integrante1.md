# Guía de pruebas — Integrante 1 (mi parte)

**Mis bloques:** presentación (0:00–1:00) + caché **C1** `Avión` 15s (4:30–5:50)
+ caché **C4** `Camión` NO_CACHE (5:50–6:50).
Requests Postman citados: `postman/taller_vehiculos.json` (importar + `entorno_local.json`).

## A. Ejecutar el proyecto

```powershell
wsl sudo service redis-server start
wsl redis-cli ping                        # -> PONG
.\venv\Scripts\Activate.ps1
python app.py                             # -> http://127.0.0.1:5000 (dejar corriendo)
```

Seed limpio (10 docs) y Redis sin mis claves (otra PowerShell):

```powershell
mongosh --file DB/01_seed_automoviles.js   # termina en countDocuments() -> 10
wsl redis-cli DEL "vehiculo:Avión"         # -> 0 o 1
```

> El 404 al abrir `/` en el navegador es normal: la app no tiene ruta raíz.
> Para comprobar que vive se usa `/health`.

## B. Rutas que observo y uso

| Ruta | Para qué | Esperado |
|---|---|---|
| `GET /health` (req. 00) | Presentación: Mongo y Redis arriba | 200 `{"mongo":"up","redis":"up"}` |
| `GET /vehiculos/Avión` (req. 07 y 08) | C1: 1er MISS + 2do HIT + expiración | 1er `mongodb`/15 → 2do `redis` → tras 16s `mongodb` |
| `GET /vehiculos/Camión` (req. 09 y 10) | C4: nunca se guarda | 2× `mongodb`, `ttl_segundos: 0` |

## C. Código que puedo explicar (breve, sin línea por línea)

En `cache.py` — la función que decide el TTL por longitud de **categoría**:

```python
def ttl_para(categoria: str) -> int:
    n = len(categoria or "")
    if n > 20:
        return 0   # NO almacenar (prioritaria)
    if n <= 5:
        return 15  # mi caso C1: "Aéreo" = 5
    if n <= 10:
        return 20
    return 40
```

Y el flujo de `GET /vehiculos/<nombre>` (`routes/vehiculos_cache.py`): busca la
clave `vehiculo:<nombre>` en Redis → si existe responde `fuente: redis`; si no,
lee Mongo, guarda con `SETEX` (solo si TTL > 0) y responde `fuente: mongodb`.
Mi frase: *"`Camión` es `Terrestre (motorizado)` = 22 caracteres: retorna 0 y la
API jamás hace `SETEX`"*.

## D. Comprobaciones en MongoDB (mongosh)

```powershell
mongosh "mongodb://localhost:27017/automoviles"
```

```js
db.vehiculos.countDocuments()                       // -> 10
db.vehiculos.findOne({ nombre: "Avión" }, { _id: 0 })
// -> categoria "Aéreo" (5) => TTL 15
db.vehiculos.findOne({ nombre: "Camión" }, { _id: 0 })
// -> categoria "Terrestre (motorizado)" (22) => NO_CACHE
```

## E. Comprobaciones en Redis (WSL)

```bash
wsl redis-cli TTL "vehiculo:Avión"    # tras el 1er GET -> 15/14/13
wsl redis-cli GET "vehiculo:Avión"    # -> JSON del Avión (almacenado ✓)
wsl redis-cli GET "vehiculo:Camión"   # -> (nil): jamás se guardó (C4 ✓)
```

## F. Comprobaciones en Postman (consumidor REST)

1. **"00 GET health"** → 200, tests `mongo`/`redis` = `up`.
2. **"07 GET Avion 1er"** → 200 `{"fuente":"mongodb","ttl_segundos":15,...}`.
3. **"08 GET Avion 2do"** → 200 `{"fuente":"redis","ttl_segundos": 1–15}`.
4. Esperar **16s** (cronómetro en cámara) → repetir **07** → `{"fuente":"mongodb"}` (expiró ✓). Decir: *"almacenamiento, consulta y expiración demostrados"*.
5. **"09 GET Camion 1er"** → 200 `{"fuente":"mongodb","ttl_segundos":0}`.
6. **"10 GET Camion 2do"** → 200 otra vez `mongodb`. Decir: *"dos GET desde Mongo y `(nil)` en Redis: la prioridad funciona"*.

## G. Si algo falla en vivo

- Siempre `redis` al empezar → claves viejas: `wsl redis-cli DEL "vehiculo:Avión"`.
- `redis: down` en `/health` → `wsl sudo service redis-server start`.
- Al terminar, dejar limpio: `wsl redis-cli DEL "vehiculo:Avión"` (sigue el Int. 2).
