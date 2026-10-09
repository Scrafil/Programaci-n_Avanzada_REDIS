# PLAN POR WAVES — Taller Flask + MongoDB + Redis (3 integrantes, multi-agente)

> Alcance del PDF: BD `automoviles`, CRUD Flask verificado en Postman, caché Redis con 4
> condiciones + invalidación, repo GitHub, video YouTube 8–12 min, entrega `.txt` en Moodle.
> Venv ya creado (`python -m venv venv`, Python 3.13.14).
> Estado verificado 2026-10-09: Redis ✅ ACTIVO en WSL (`wsl redis-cli ping` → PONG) ·
> `mongosh` 2.7.0 OK pero **sin servidor Mongo local** (ECONNREFUSED; Docker apagado).

---

## 0. Decisiones técnicas congeladas (contrato — ningún agente puede cambiarlas sin QA)

### 0.1 Esquema MongoDB (imagen → código)
Colección `vehiculos` en BD `automoviles`. Campos (sin tildes en código para evitar bugs):

| Código (app/seed) | Imagen        | Tipo  | Ejemplo                                  |
|-------------------|---------------|-------|------------------------------------------|
| `nombre`          | Vehículo      | str PK| `"Barco"` (clave de búsqueda y de caché) |
| `categoria`       | Categoría     | str   | `"Acuático"` (**campo identificador**)   |
| `peso_toneladas`  | Peso (ton.)   | float | `500`                                    |
| `descripcion`     | Descripción   | str   | `"Embarcación grande usada …"`           |

Índice único: `{ nombre: 1 }`. Seed exacto: `DB/01_seed_automoviles.js` (10 docs).

### 0.2 Contrato API (Postman debe probar exactamente esto)
| Método | Ruta                  | Respuesta caché |
|--------|-----------------------|-----------------|
| POST   | `/vehiculos`          | crea, **no** lee caché |
| GET    | `/vehiculos`          | lista desde Mongo (sin caché de lista) |
| GET    | `/vehiculos/<nombre>` | `{ ..., "fuente": "mongodb" \| "redis", "ttl_segundos": N }` (TTL según su `categoria`) |
| PUT    | `/vehiculos/<nombre>` | actualiza + `DEL vehiculo:<nombre>` en Redis |
| DELETE | `/vehiculos/<nombre>` | elimina + `DEL vehiculo:<nombre>` en Redis |
| GET    | `/health`             | `{ mongo, redis }` para diagnóstico en video |

### 0.3 Regla de caché (única fuente de verdad, Python)
```python
CAMPO_IDENTIFICADOR = "categoria"

def ttl_para(categoria: str) -> int:
    n = len(categoria or "")
    if n > 20:   # PRIORITARIA (equivale a "descripción superior a 20")
        return 0  # 0 = NO almacenar en caché
    if n <= 5:  return 15
    if n <= 10: return 20
    return 40
```
Clave Redis: `vehiculo:<nombre>` (búsqueda por nombre, TTL por su categoría),
valor JSON del documento, `SETEX` con el TTL. `fuente: "redis"` solo si hubo HIT;
si no, Mongo + `SETEX` (si TTL > 0).

### 0.4 Decisión del equipo: campo identificador = `categoria` (defensa para el video)
El PDF deja abierto cuál es "el campo que identifica al vehículo". El equipo fija
`categoria`, porque es la **única lectura con la que el seed ejercita las condiciones**.
Longitudes verificadas (Python + `$strLenCP`):

| Categoria | Chars | TTL | Vehículos seed |
|---|---|---|---|
| `Aéreo` | 5 | **15s (C1)** | Avión, Helicóptero |
| `Acuático` | 8 | **20s (C2)** | Barco, Lancha |
| `Espacial` | 8 | **20s (C2)** | Cohete |
| `Terrestre (motorizado)` | 22 | **NO_CACHE (C4)** | Automóvil, Motocicleta, Camión |
| `Terrestre (no motorizado)` | 25 | **NO_CACHE (C4)** | Bicicleta, Monopatín |
| `Acuático ligero` (solo `DB/03`) | 15 | **40s (C3)** | Hidroavión (dato de prueba) |

La condición C3 (11–20 chars) no tiene ejemplo en el seed: se demuestra con **un solo**
documento de prueba (`DB/03_dato_prueba_c3.js`). Frase para el video: *"Tomamos la
categoría como campo identificador; así, los datos reales de la tabla cubren tres de
las cuatro condiciones y solo la de 40 segundos requiere un dato adicional"*.

---

## 1. Reparto de sustentación (3 personas, video 8–12 min, objetivo 10:30)

| Bloque (min) | Dueño | Tema | Demo en vivo |
|---|---|---|---|
| 0:00–1:00 | **TÚ (Int. 1)** | Presentación, objetivo, arquitectura (Flask→Mongo/Redis WSL) | Diagrama / `/health` |
| 1:00–2:30 | Int. 2 | Estructura MongoDB + seed | `mongosh` + `DB/02` consultar/agregar |
| 2:30–4:30 | Int. 3 | CRUD completo en Postman | POST→GET→PUT→DELETE + `DB/02` |
| 4:30–5:50 | **TÚ (Int. 1)** | Caché **C1** (`Aéreo`=5 → 15s) + expiración | `GET /vehiculos/Avión` ×2 (mongodb→redis), esperar 15s, vuelve a mongodb |
| 5:50–6:50 | **TÚ (Int. 1)** | Caché **C4** (`Terrestre…`=22/25 → NO guarda, prioritaria) | `GET /vehiculos/Camión` ×2: siempre `mongodb`; explicar por qué |
| 6:50–8:00 | Int. 2 | Caché **C2** (`Acuático`/`Espacial`=8 → 20s) + **invalidación PUT/DELETE** | `GET Barco`, `PUT`, `GET` (miss), `TTL` en Redis |
| 8:00–9:20 | Int. 3 | Caché **C3** (`Acuático ligero`=15 → 40s) + expiración + `fuente` | `GET Hidroavión`, `TTL`, conclusiones |
| 9:20–10:30 | Int. 3 + Tú | Conclusiones + GitHub/Moodle/entrega | Repo, `requirements.txt`, `.txt` Moodle |

Cada uno **explica y demuestra** sección distinta (exigencia del PDF §5).

---

## 2. Mapa de Waves (orden + paralelismo)

```
Wave 0  ✅ HECHO                  .env(.example), DB/01 .js + DB/02 y DB/03 .txt, este plan. Redis WSL verificado (PONG).
Wave 1  🔵 PARALELO (3 agentes)     Infra+esqueleto · Contrato Postman · Verificación BD
Wave 2  🟣 PARALELO (2 agentes)     API CRUD · Capa caché Redis   (propiedad de archivos estricta)
Wave 3  🟢 SECUENCIAL (1-2 agentes) Integración E2E + QA TTL reales + README + GitHub
Wave 4  👥 HUMANOS                  Ensayo + grabación + entrega Moodle
```

Regla anti-colisiones: cada agente solo toca los archivos de su columna. `app.py`
(esqueleto) lo congela Wave 1 y solo lo extienden por import en Wave 2.

> ⚠️ Pendiente de infra: **MongoDB** aún sin servidor (local ECONNREFUSED, Docker
> apagado). Opción A: encender Docker Desktop y usar `docker-compose.yml` (Wave 1).
> Opción B: Atlas en `.env` local (no commitear). **Redis**: usar el de WSL
> (`localhost:6379` visible desde Windows); arrancar con `wsl sudo service redis-server start`
> tras cada reinicio. El agente W1-A debe dejar esto documentado en README.

---

## 3. WAVE 1 — Fundaciones (3 agentes en paralelo, sin dependencias entre sí)

### 🤖 Agente W1-A «Infra & Esqueleto» — archivos: `requirements.txt`, `docker-compose.yml`, `.gitignore`, `config.py`, `app.py` (solo health), `README.md` (borrador)
```text
Rol: Infra/Backend. Directorio: taller_Redis_Programacion/.
Contexto: venv ya existe (Python 3.13.14). Redis ACTIVO en WSL (localhost:6379,
verificado con PONG; se arranca con `wsl sudo service redis-server start`).
MongoDB SIN servidor: deja docker-compose.yml (mongo:7) como opción A y documenta
Atlas como opción B en README. NO cambies el .env commiteado salvo el ejemplo.
CONTRATO INAMOVIBLE (PLAN_WAVES.md §0): BD automoviles, colección vehiculos,
campos nombre/categoria/peso_toneladas/descripcion, CAMPO_IDENTIFICADOR=categoria,
TTL 15/20/40/0 por len(categoria) con prioridad >20, clave vehiculo:<nombre>,
endpoints y campo fuente/ttl_segundos.
Tareas:
1. requirements.txt: Flask, pymongo, redis, python-dotenv (fija versiones).
2. config.py: lee .env (MONGO_URI/DB/COLLECTION, REDIS_HOST/PORT/DB o REDIS_URL,
   FLASK_PORT, CAMPO_IDENTIFICADOR, CACHE_KEY_PREFIX) con defaults del .env.
3. app.py mínimo: factory Flask, GET /health que reporta {mongo, redis} reales,
   errores JSON. NO agregues CRUD ni caché (Wave 2).
4. docker-compose.yml: mongo:7 + redis:7 (el redis local es el de WSL; el servicio
   compose es alternativa) con volúmenes y puertos 27017/6379.
5. .gitignore: venv/, .env, __pycache__/.
6. README.md borrador: venv+pip, cómo arrancar Redis WSL, Docker vs Atlas,
   seed y demos (`mongosh --file DB/01_seed_automoviles.js`, luego copiar/pegar
   `DB/02_consultas_demo.txt` y Parte A de `DB/03_dato_prueba_c3.txt`) y `python app.py`.
Hecho cuando: `pip install -r requirements.txt` OK, `python app.py` levanta y
/health responde JSON con redis=up (WSL); `docker-compose config` válido.
Prohíbo: tocar DB/, .env, crear endpoints CRUD o lógica Redis.
```
### 🤖 Agente W1-B «Contrato Postman» — archivos: `postman/` (colección + entorno)
```text
Rol: QA/Contrato. Directorio: taller_Redis_Programacion/.
Lee PLAN_WAVES.md §0.2–§0.4 (identificador=categoria) y crea, SIN esperar al
backend (contract-first):
1. postman/taller_vehiculos.json: colección v2.1 en orden de video: health,
   GET lista, GET Avión (C1 15s), GET Camión (C4 0), GET Barco (C2 20s),
   PUT Barco, GET Barco (miss post-invalidación), POST/GET Hidroavión (C3 40s,
   body y secuencia fuente en `DB/03_dato_prueba_c3.txt` Parte C),
   DELETE Hidroavión, con tests que asertan `fuente` y `ttl_segundos`
   (15/20/40/0 según §0.4).
2. postman/entorno_local.json: {{base_url}}=http://localhost:5000.
3. Cada request lleva descripción de 1 línea: condición que demuestra + dueño
   (Int.1 C1+C4, Int.2 C2, Int.3 C3).
Hecho cuando: colección importa en Postman sin errores y el orden coincide con
la tabla de tiempos §1.
Prohíbo: tocar app.py, config.py, DB/, requirements.
```
### 🤖 Agente W1-C «Verificación BD» — archivos: ninguno nuevo (reporte en chat)
```text
Rol: DBA/QA. Directorio: taller_Redis_Programacion/.
Tareas (solo lectura + reporte, NO modificar seed):
1. Requiere Mongo levantado (Docker o Atlas según README de W1-A; si no hay,
   repórtalo y NO bloquees: verifica solo sintaxis con mongosh --nodb si aplica).
2. Ejecutar en orden `DB/01_seed_automoviles.js`, `DB/02_consultas_demo.txt`
   y Parte A de `DB/03_dato_prueba_c3.txt`; verificar: 10 docs seed, índice único
   nombre, matriz §4 de DB/02 = 15s Avión/Helicóptero, 20s Barco/Lancha/Cohete,
   0 Automóvil/Motocicleta/Camión/Bicicleta/Monopatín, 40s solo Hidroavión.
3. Verificar que `wsl redis-cli ping` sigue en PONG.
Hecho cuando: reporte OK/FAIL por check + salida de las agregaciones.
Prohíbo: crear/editar cualquier archivo del repo.
```

---

## 4. WAVE 2 — Núcleo (2 agentes en paralelo, propiedad de archivos estricta)

> Pre-requisito: Wave 1 mergeado. Ambos parten del mismo `app.py`+`config.py`.

### 🤖 Agente W2-API «CRUD Flask» — archivos: `routes/vehiculos.py` (+ `models.py` si quiere), edita `app.py` SOLO para registrar el blueprint
```text
Rol: Backend. Contrato §0.1/§0.2 inamovible (identificador=categoria, clave=nombre).
Implementa con PyMongo (sin ODM): POST /vehiculos (201, valida los 4 campos,
409 si nombre duplicado), GET /vehiculos (lista), PUT /vehiculos/<nombre>
(200/404), DELETE /vehiculos/<nombre> (200/404). GET individual lo implementa
W2-CACHE: NO lo toques; si existe stub, déjalo. PUT/DELETE deben llamar a
`cache.invalidar(nombre)` (try/except por si W2-CACHE aún no mergea). JSON siempre.
Hecho cuando: CRUD pasa contra Mongo real usando un vehículo temporal propio
(crear/leer/actualizar/borrar; NO borrar el Hidroavión de DB/03) y lista final íntegra.
Prohíbo: tocar cache.py, postman/, DB/, .env.
```
### 🤖 Agente W2-CACHE «Redis» — archivos: `cache.py` (+ `GET /vehiculos/<nombre>` en `routes/vehiculos_cache.py` o función usada por app.py)
```text
Rol: Backend/Caché. Contrato §0.3/§0.4 inamovible. Dueño de TODA la lógica Redis.
Redis vive en WSL (localhost:6379); verifica con `wsl redis-cli ping`.
Implementa en cache.py: ttl_para(categoria) EXACTO al §0.3,
get_vehiculo(nombre, mongo_getter) -> (doc, fuente, ttl) con flujo:
GET vehiculo:<nombre> -> HIT: fuente=redis (+TTL restante) |
MISS: leer Mongo (404 si no existe), ttl=len(categoria): si 0 devolver
fuente=mongodb SIN guardar; si no SETEX JSON + fuente=mongodb.
invalidar(nombre) -> DEL (llamado por PUT/DELETE).
Exponer GET /vehiculos/<nombre>: doc + fuente + ttl_segundos.
Guion a verificar: 1er GET Avión=mongodb, 2do=redis, tras 15s=mongodb;
2 GET Camión=mongodb siempre; documenta cómo ver TTL (respuesta + `wsl redis-cli TTL`)
para el video.
Hecho cuando: matriz C1=15/C2=20/C3=40/C4=0 verificada con tiempos REALES
(cronometrados ±2s) + invalidación PUT/DELETE demostrada.
Prohíbo: tocar el CRUD de W2-API salvo el punto de invalidación acordado,
postman/, DB/, .env.
```

---

## 5. WAVE 3 — Integración + QA + GitHub (1 agente, luego 1 revisor)

### 🤖 Agente W3 «E2E + QA + Release» — archivos: `tests/`, `README.md` (final), `entrega_moodle.txt`
```text
Rol: QA/Release. Pre-requisito: Waves 1-2 mergeados, Mongo levantado, Redis WSL
en PONG (`wsl sudo service redis-server start` si hizo falta).
1. E2E: seed limpio (`DB/01_seed_automoviles.js`) + Parte A de DB/03, recorrer
   TODA la colección Postman y anotar fuente/ttl de cada GET (esperado §0.4). 2. QA de tiempos reales: 15s (Avión),
   20s (Barco), 40s (Hidroavión: vale mostrar TTL restante + 2º GET), C4
   (2×Camión=mongodb) + invalidación PUT/DELETE; tabla PASS/FAIL con segundos.
   3. README final: venv+pip, Redis WSL, Docker/Atlas, seed mongosh, run, orden
   Postman, tabla §0.4 + frase de defensa del identificador, integrantes y
   enlaces (placeholders GitHub/YouTube). 4. GitHub público sin .env
   (solo .env.example). 5. entrega_moodle.txt: nombres + 2 enlaces.
Hecho cuando: 0 FAIL y un tercero puede levantar todo desde cero con el README.
```
### 🤖 Agente W3-R «Revisor» (5 min, otra sesión)
```text
Rol: QA independiente. Verifica: GET Avión/Barco/Hidroavión/Camión dan
15/20/40/0; PUT/DELETE invalidan; seed intacto salvo Hidroavión; .env fuera de
git (git ls-files); README ejecutable. Reporta GO/NO-GO.
```

---

## 6. WAVE 4 — Humanos (ensayo y grabación, no delegable a agentes)

1. Ensayo con cronómetro (10:30 objetivo, nunca <8 ni >12).
2. C1 (15s) se espera en cámara real; 20/40s: mostrar TTL restante + corte
   "tras X s…" + 2º GET con el tiempo medido en Wave 3.
3. YouTube (no listado), push final, `.txt` a Moodle.

---

## 7. Definición de HECHO global (checklist de aceptación del taller)
- [ ] `automoviles.vehiculos` con 10 docs + índice único (DB/01).
- [ ] CRUD Postman en verde (POST/GET/PUT/DELETE + §0.2).
- [ ] GET individual devuelve `fuente` mongodb|redis + `ttl_segundos` (TTL por `categoria`).
- [ ] TTL reales 15/20/40 medidos ±2s; `Terrestre…` (22/25) nunca se guarda.
- [ ] PUT/DELETE invalidan (`DEL`) — demostrado en video.
- [ ] Evidencia de almacenamiento, consulta y expiración en Redis (§3 PDF).
- [ ] GitHub público con README ejecutable; video 8–12 min con los 3 participando.
- [ ] `.txt` Moodle con nombres + 2 enlaces funcionales.
