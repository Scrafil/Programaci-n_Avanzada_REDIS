# Taller: API REST Flask + MongoDB + Redis (caché con TTL por categoría)

CRUD de vehículos (BD `automoviles`, colección `vehiculos`) con caché en Redis.
Al consultar un vehículo se devuelve `fuente: mongodb|redis` y `ttl_segundos`.

## 1. Regla de caché (contrato §0.3 del plan)

Campo identificador: **`categoria`**. TTL por `len(categoria)`:

| Banda | Ejemplo | TTL |
|---|---|---|
| `<=5` | `Aéreo` (Avión, Helicóptero) | 15s |
| `6-10` | `Acuático` (Barco, Lancha), `Espacial` (Cohete) | 20s |
| `11-20` | `Acuático ligero` (Hidroavión, dato POST) | 40s |
| `>20` (prioritaria) | `Terrestre (motorizado)` (22), `Terrestre (no motorizado)` (25) | no se guarda |

Clave Redis `vehiculo:<nombre>` con `SETEX`. PUT/DELETE hacen `DEL` (invalidan).
Frase de defensa: *"Tomamos la categoría como campo identificador; así, los datos
reales de la tabla cubren tres de las cuatro condiciones y solo la de 40 segundos
requiere un dato adicional".*

## 2. Instalación

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # ajustar solo si usan Atlas / Redis Cloud
```

## 3. Servicios

**Redis:** corre en Ubuntu-WSL (verificado v8.0.5). Tras cada reinicio:

```powershell
wsl sudo service redis-server start
wsl redis-cli ping            # -> PONG
wsl redis-cli TTL "vehiculo:Barco"   # TTL restante de una clave
```

**MongoDB:** opción A `docker compose up -d` (servicio `mongo:7`); opción B Atlas
en el `.env` local (el `.env` nunca se commitea).

## 4. Seed y demos

```powershell
mongosh "mongodb://localhost:27017/automoviles" --file DB/01_seed_automoviles.js
```

- `DB/01_seed_automoviles.js` — crea BD + colección con validador, 10 vehículos,
  índice único `nombre` (no modificar; idempotente).
- `DB/02_consultas_demo.txt` — guía de pruebas del **Integrante 1** (C1 + C4).
- `DB/03_dato_prueba_c3.txt` — dato C3 en 3 lenguajes (mongosh + redis-cli + HTTP).
- `DB/04_guia_integrante2.txt` — guía del **Integrante 2** (Mongo + C2 + invalidación).
- `DB/05_guia_integrante3.txt` — guía del **Integrante 3** (CRUD + C3 + conclusiones).

## 5. API

```powershell
python app.py   # http://localhost:5000
```

| Método | Ruta | Notas |
|---|---|---|
| `POST` | `/vehiculos` | 201, 409 si `nombre` duplicado, 400 si faltan campos |
| `GET` | `/vehiculos` | lista desde Mongo |
| `GET` | `/vehiculos/<nombre>` | doc + `fuente` + `ttl_segundos` (404 si no existe) |
| `PUT`/`DELETE` | `/vehiculos/<nombre>` | 200/404 + invalidan caché |
| `GET` | `/health` | `{"status","mongo","redis","db"}` |

Postman: importar `postman/taller_vehiculos.json` + `postman/entorno_local.json`
y correr en orden (20 requests; deja el seed intacto).

## 6. Tests

```powershell
python -m unittest              # rápidos (matriz TTL + CRUD + MISS/HIT/invalidación)
E2E_SLOW=1 python -m unittest   # + expiración real C1 (~16s)
```

## 7. Evidencia QA medida (E2E 2026-10-09, 27/27 PASS)

| Caso | Resultado |
|---|---|
| `GET /health` | mongo up, redis up |
| `GET /vehiculos` | 10 docs seed |
| CRUD `E2ETemp` | POST 201 → GET mongodb/15 → PUT 200 → DELETE 200 → GET 404 |
| C1 `Avión` | MISS mongodb/15, `TTL`=15, HIT redis (restante 13), tras espera 18.1s → mongodb |
| C4 `Camión` | 2× mongodb/0, `GET vehiculo:Camión` → nil |
| C2 `Barco` | MISS mongodb/20, HIT redis, PUT 2.5 → GET mongodb (dato nuevo), expiración tras 21s → mongodb |
| C3 `Hidroavión` | POST 201, MISS mongodb/40, `TTL`=40, HIT redis, tras espera 43.0s → mongodb, DELETE |
| Estado final | 10 docs, 0 claves `vehiculo:*` |

## 8. Equipo y entrega

- Integrantes: _pendiente (3)_.
- GitHub: _pendiente_ · Video YouTube (8–12 min): _pendiente_.
- Moodle: un `.txt` con nombres + ambos enlaces (`entrega_moodle.txt` como plantilla).
