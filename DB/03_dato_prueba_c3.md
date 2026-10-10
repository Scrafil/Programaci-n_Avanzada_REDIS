# Dato de prueba C3 + demos en 3 lenguajes

## ¿Para qué sirve este archivo?

La banda **C3** (categoría de 11–20 caracteres → TTL **40s**) **no tiene ningún
ejemplo en el seed**: todas las categorías semilla miden 5, 8, 22 o 25. Por eso
este archivo crea **un solo documento** (`Hidroavión`, categoría
`Acuático ligero` = 15 caracteres) y muestra cómo demostrar su caché en
**mongosh**, **redis-cli** y **Postman**. Dueño de la demo: **Integrante 3**.
El seed de 10 vehículos no se modifica (ver limpieza al final).

## Parte A — MongoDB (mongosh): crear el dato

Copiar este bloque en `mongosh "mongodb://localhost:27017/automoviles"`:

```js
db.vehiculos.deleteOne({ nombre: "Hidroavión" }); // idempotente
db.vehiculos.insertOne({
  nombre: "Hidroavión",
  categoria: "Acuático ligero", // 15 caracteres -> TTL 40s
  peso_toneladas: 4,
  descripcion: "Avión que acuatiza."
});

db.vehiculos.aggregate([
  { $project: { _id: 0, nombre: 1, categoria: 1,
    ttl_esperado_s: { $switch: { branches: [
      { case: { $gt: [{ $strLenCP: "$categoria" }, 20] }, then: 0 },
      { case: { $lte: [{ $strLenCP: "$categoria" }, 5] }, then: 15 },
      { case: { $lte: [{ $strLenCP: "$categoria" }, 10] }, then: 20 } ],
      default: 40 } } } } },
  { $sort: { ttl_esperado_s: 1, nombre: 1 } }
]).toArray();
// Esperado: 15s Avión/Helicóptero | 20s Barco/Lancha/Cohete | 40s Hidroavión
//           0 (NO_CACHE) Automóvil/Motocicleta/Camión/Bicicleta/Monopatín
```

## Parte B — Redis (redis-cli en Ubuntu-WSL): demostrar el caché

Entre cada `GET` de la API y cada comando, usar Postman o
`curl http://localhost:5000/vehiculos/Hidroavi%C3%B3n`:

```bash
redis-cli DEL "vehiculo:Hidroavión"      # punto de partida limpio -> 0 o 1

# 1er GET /vehiculos/Hidroavión -> fuente=mongodb (MISS, guarda con 40s)
redis-cli GET "vehiculo:Hidroavión"      # -> JSON del documento
redis-cli TTL "vehiculo:Hidroavión"      # -> ~40 (entre 38-40)

# 2do GET /vehiculos/Hidroavión -> fuente=redis (HIT)
redis-cli TTL "vehiculo:Hidroavión"      # -> menor: el tiempo corre

# Expiración: esperar 40s y repetir
redis-cli GET "vehiculo:Hidroavión"      # -> (nil): expiró
# 3er GET -> fuente=mongodb de nuevo (re-cachea)

# Invalidación (misma técnica del PUT del Integrante 2):
redis-cli GET "vehiculo:Hidroavión"      # -> (nil) tras un PUT

# Utilidad de evidencia en video:
redis-cli KEYS "vehiculo:*"             # claves vivas en ese instante
```

## Parte C — Postman / HTTP: secuencia de la demo C3

```http
POST /vehiculos
Content-Type: application/json

{"nombre":"Hidroavión","categoria":"Acuático ligero","peso_toneladas":4,"descripcion":"Avión que acuatiza."}
```

- `GET /vehiculos/Hidroavión` (1ra vez) → `{"fuente":"mongodb","ttl_segundos":40}`
- `GET /vehiculos/Hidroavión` (2da vez) → `{"fuente":"redis",...}`
- (esperar 40s) `GET` → `{"fuente":"mongodb",...}` otra vez

Secuencia completa del video por dueño:

- **Int. 1:** `GET Avión` ×2 (mongodb→redis, 15s) + esperar 15s + `GET` (mongodb)
- **Int. 1:** `GET Camión` ×2 (siempre mongodb: NO_CACHE, 22 chars)
- **Int. 2:** `GET Barco` ×2 (mongodb→redis, 20s) + PUT 500→501 + `GET` (mongodb) + PUT restaura 500
- **Int. 3:** `GET Hidroavión` ×2 (mongodb→redis, 40s) + TTL + expiración

## Limpieza post-demo (mongosh, deja solo el seed)

```js
db.vehiculos.deleteOne({ nombre: "Hidroavión" });
```
