# Guía de pruebas — Integrante 2

**Bloques:** estructura MongoDB (1:00–2:30) + caché **C2** `Barco` 20s e
invalidación PUT/DELETE (6:50–8:00). Requests Postman 01 y 11–15.
Requisito previo: proyecto corriendo (ver PASO 0 de `DB/02_guia_integrante1.md`).

## 1. Estructura MongoDB en mongosh (1:00–2:30)

```powershell
mongosh "mongodb://localhost:27017/automoviles"
```

**a) Un documento de ejemplo** (qué campos tiene):

```js
db.vehiculos.findOne({ nombre: "Barco" }, { _id: 0 })
// -> { nombre, categoria: "Acuático", peso_toneladas: 500, descripcion }
```

Decir: *"Cuatro campos; `nombre` es clave con índice único y `categoría` es el
campo identificador del caché."*

**b) Conteo por categoría:**

```js
db.vehiculos.aggregate([
  { $group: { _id: "$categoria", total: { $sum: 1 } } },
  { $sort: { _id: 1 } }
]).toArray()
// -> Aéreo 2, Acuático 2, Espacial 1,
//    Terrestre (motorizado) 3, Terrestre (no motorizado) 2. Total 10.
```

**c) Matriz de caché** (lógica espejo de la API, evidencia de las bandas):

```js
db.vehiculos.aggregate([
  { $project: { _id: 0, nombre: 1,
    ttl_esperado_s: { $switch: { branches: [
      { case: { $gt: [{ $strLenCP: "$categoria" }, 20] }, then: 0 },
      { case: { $lte: [{ $strLenCP: "$categoria" }, 5] }, then: 15 },
      { case: { $lte: [{ $strLenCP: "$categoria" }, 10] }, then: 20 } ],
      default: 40 } } } } },
  { $sort: { ttl_esperado_s: 1, nombre: 1 } }
]).toArray()
// -> 15s Avión/Helicóptero; 20s Barco/Lancha/Cohete; 0 los 5 Terrestre.
```

Decir: *"El seed cubre C1, C2 y C4; C3 la demuestra el Integrante 3."*

## 2. C2: `GET Barco` MISS + HIT (6:50–8:00)

```bash
wsl redis-cli DEL "vehiculo:Barco"      # punto de partida limpio
```

- Postman **"11 GET Barco 1er"** → `GET /vehiculos/Barco` → 200
  `(fuente mongodb, ttl 20)`. Decir: *"`Acuático` mide 8, banda de 20s. MISS."*
- `wsl redis-cli TTL "vehiculo:Barco"` → esperado 18–20.
- Postman **"12 GET Barco 2do"** → 200 `(fuente redis)`. Decir: *"HIT, el TTL corre."*

## 3. Invalidación con PUT (evidencia fuerte)

- Postman **"13 PUT Barco invalida cache"** → `PUT /vehiculos/Barco` con:

```json
{"categoria": "Acuático", "peso_toneladas": 501, "descripcion": "Embarcación grande usada para transporte marítimo."}
```

→ esperado 200.

- `wsl redis-cli GET "vehiculo:Barco"` → esperado `(nil)`: el PUT hizo `DEL`.
- Postman **"14 GET Barco tras PUT"** → 200 `(fuente mongodb, peso 501)`.
  Decir: *"Al actualizar se invalida la caché: MISS con el dato nuevo. Sin esto
  habría inconsistencias."*
- **Restaurar el seed (obligatorio):** Postman **"15 PUT Barco restaura seed"**
  (peso 500, descripción original) → 200, y verificar:

```js
db.vehiculos.findOne({ nombre: "Barco" }, { _id: 0 })
// -> peso_toneladas debe volver a 500
```

Fin de tu parte. Sigue el Integrante 3 (`DB/05_guia_integrante3.md`).
