# Guía de pruebas — Integrante 3

**Bloques:** CRUD Postman (2:30–4:30) + C3 `Hidroavión` 40s (8:00–9:20) +
conclusiones y entrega (9:20–10:30). Requests 01–06 y 16–19.
Requisito previo: proyecto corriendo (ver PASO 0 de `DB/02_guia_integrante1.md`).

## 1. CRUD completo en Postman (2:30–4:30)

| Request | Petición | Esperado |
|---|---|---|
| 01 | `GET /vehiculos` | 200 con 10 docs |
| 02 | `POST /vehiculos` `{"nombre":"PruebaCRUD","categoria":"Aéreo","peso_toneladas":1,"descripcion":"Prueba CRUD."}` | 201 (409 si se repite: normal) |
| 03 | `GET /vehiculos/PruebaCRUD` | 200 (mongodb, ttl 15) |
| 04 | `PUT /vehiculos/PruebaCRUD` `{"peso_toneladas":2}` | 200 (peso 2) |
| 05 | `DELETE /vehiculos/PruebaCRUD` | 200 |
| 06 | `GET /vehiculos/PruebaCRUD` | 404 (eliminación real) |

Decir: *"POST crea (201), GET lee, PUT actualiza, DELETE elimina y el 404 lo
prueba. La lista vuelve a 10: seed intacto."* Si `01` muestra 11 docs, otro
integrante dejó un `Hidroavión`: borrarlo con el request 19 antes de seguir.

## 2. C3: crear el dato 40s vía POST (8:00–9:20)

Request **16**: `POST /vehiculos` con:

```json
{"nombre": "Hidroavión", "categoria": "Acuático ligero", "peso_toneladas": 4, "descripcion": "Avión que acuatiza."}
```

→ esperado 201 (409 si ya existe: seguir igual).
Decir: *"La banda 11–20 no existe en el seed; la creamos con la propia API:
`Acuático ligero` mide 15, TTL 40."* (Detalle del porqué: `DB/03_dato_prueba_c3.md`.)

## 3. C3: MISS + HIT + expiración (estrategia 40s)

- Request **17**: `GET /vehiculos/Hidroavión` → 200 `(mongodb, ttl 40)`.
- `wsl redis-cli TTL "vehiculo:Hidroavión"` → esperado 38–40.
- Request **18**: mismo GET → 200 `(fuente redis)`.
- **Estrategia de video** (40s es largo): mostrar el TTL restante, anunciar corte
  *"tras 40 segundos…"* y mostrar el GET final → 200 `(mongodb)` otra vez.
  Decir: *"MISS, HIT y expiración: el ciclo completo del caché."*
- **Limpieza obligatoria:** request **19** (`DELETE Hidroavión` → 200) y verificar:

```js
db.vehiculos.countDocuments()   // -> 10
```

## 4. Conclusiones y entrega (9:20–10:30)

Mostrar: repo GitHub público (README ejecutable, `.env` fuera por `.gitignore`) y
tests en verde:

```powershell
python -m unittest   # -> OK (13 tests, 1 omitido: expiración lenta)
```

Decir (~60s): *"MongoDB guarda con esquema e índice único; Redis acelera
lecturas con TTL por categoría e invalidación en PUT/DELETE; la banda >20
prioritaria evita cachear lo descriptivo. Tres condiciones con datos reales y la
cuarta con un POST: cumplimiento total del taller."* Cierre con nombres + repo +
video; el `.txt` de Moodle sale de `entrega_moodle.txt`.
