# Taller: API REST Flask + MongoDB + Redis (caché con TTL por categoría)

CRUD de vehículos (BD `automoviles`, colección `vehiculos`) con caché en Redis.
Al consultar un vehículo se devuelve `fuente: mongodb|redis` y `ttl_segundos`.

## 1. Cómo funciona (resumen)

```text
Postman ──HTTP──▶ app.py (Flask) ──┬──▶ routes/vehiculos.py ──▶ MongoDB (datos)
                                   └──▶ routes/vehiculos_cache.py + cache.py ──▶ Redis (copia con TTL)
```

- `GET /vehiculos/<nombre>`: busca `vehiculo:<nombre>` en Redis (HIT → `redis`);
  si no está, lee Mongo, guarda con `SETEX` y responde `mongodb` (MISS).
- `PUT`/`DELETE`: actualizan/borran en Mongo y hacen `DEL` (invalidan).
- `GET /vehiculos` (lista) nunca toca Redis. `GET /health` reporta el estado.

## 2. Regla de caché

Campo identificador: **`categoria`**. TTL por `len(categoria)`:

| Banda | Ejemplo | TTL |
|---|---|---|
| `<=5` | `Aéreo` (Avión, Helicóptero) | 15s |
| `6-10` | `Acuático` (Barco, Lancha), `Espacial` (Cohete) | 20s |
| `11-20` | `Acuático ligero` (Hidroavión, dato POST) | 40s |
| `>20` (prioritaria) | `Terrestre (motorizado)` (22), `Terrestre (no motorizado)` (25) | no se guarda |

## 3. Requisitos

- Python 3.13 + venv (incluido en el repo).
- MongoDB en local (servicio Windows) + **MongoDB Compass** para verlo.
- App **Ubuntu** (Microsoft Store) con `redis-server` para el caché.
- **Postman** para consumir la API.

## 4. Instalación (desde cero)

```powershell
cd C:\Users\joans\Downloads\taller_programacion_redis\taller_Redis_Programacion
python -m venv venv                   # solo si no existe
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt       # Flask, pymongo, redis, python-dotenv
copy .env.example .env                # ajustar solo si usan Atlas / Redis Cloud
```

## 5. Servicios y seed

En la app **Ubuntu** (tras cada reinicio):

```bash
sudo service redis-server start
redis-cli ping                        # -> PONG
```

MongoDB corre como servicio local; verifícalo en Compass (`mongodb://localhost:27017`).
Alternativa Docker: `docker compose up -d` (servicio `mongo:7`).

Seed (10 vehículos + índice único `nombre`), en PowerShell o Ubuntu:

```powershell
mongosh --file DB/01_seed_automoviles.js   # -> al final: 10
```

## 6. Ejecución y uso

```powershell
python app.py                         # http://localhost:5000 (dejar abierto)
```

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/health` | `{"status","mongo","redis","db"}`: ¿vive cada servicio? (`/` no existe: su 404 es normal) |
| `GET` | `/vehiculos` | lista desde Mongo (sin caché) |
| `GET` | `/vehiculos/<nombre>` | doc + `fuente` + `ttl_segundos` (404 si no existe) |
| `POST` | `/vehiculos` | crear con body JSON (201, 409 duplicado, 400 incompleto) |
| `PUT`/`DELETE` | `/vehiculos/<nombre>` | 200/404 + invalidan caché |

**Postman:** Import → `postman/taller_vehiculos.json` + `postman/entorno_local.json`
→ entorno **Taller Local**. El método va en el desplegable y en la barra solo la
URL (`{{base_url}}` se reemplaza sola); los POST/PUT llevan Body → raw → JSON.
Correr los 20 requests en orden deja el seed intacto.

**Probar el caché a mano:** `GET /vehiculos/Avión` (Postman, `mongodb`/15) →
`redis-cli TTL "vehiculo:Avión"` (Ubuntu, ~15) → mismo GET (`redis`) → esperar
16s → mismo GET (`mongodb`: expiró y se re-guardó solo).

**Guías por integrante:** `DB/02_guia_integrante1.md` (C1 + C4),
`DB/04_guia_integrante2.md` (Mongo + C2 + invalidación),
`DB/05_guia_integrante3.md` (CRUD + C3 + conclusiones).

## 7. Tests

```powershell
python -m unittest              # rápidos (matriz TTL + CRUD + MISS/HIT/invalidación)
E2E_SLOW=1 python -m unittest   # + expiración real C1 (~16s)
```

## 8. Evidencia QA medida (E2E 27/27 PASS + suite 13 OK)

| Caso | Resultado |
|---|---|
| `GET /health` | mongo up, redis up |
| `GET /vehiculos` | 10 docs seed |
| C1 `Avión` | MISS mongodb/15, `TTL`=15, HIT redis, tras espera 18.1s → mongodb |
| C4 (`Camión` seed y `Taxi` POST) | siempre mongodb/0, `GET` en Redis → nil |
| C2 `Barco` | MISS mongodb/20, HIT redis, PUT 501 → GET mongodb (dato nuevo), expiración tras 21s → mongodb |
| C3 `Hidroavión` | POST 201, MISS mongodb/40, `TTL`=40, HIT redis, tras espera 43.0s → mongodb, DELETE |
| Estado final | 10 docs, 0 claves `vehiculo:*` |

