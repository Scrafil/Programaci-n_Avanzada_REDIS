// ============================================================
// DB/01_seed_automoviles.js — CREACIÓN COMPLETA de la BD en MongoDB
// Crea la BD `automoviles`, la colección `vehiculos` (con validador de
// esquema), inserta los 10 vehículos de la imagen y el índice único.
// Es idempotente: borra la colección y la reconstruye cada vez.
// Ejecutar con:
//   mongosh "mongodb://localhost:27017/automoviles" --file DB/01_seed_automoviles.js
// ============================================================
const DB_NAME = "automoviles";
const COLL = "vehiculos";
const dbx = db.getSiblingDB(DB_NAME);

// ---- 1) Limpieza (la BD se crea sola al insertar el primer documento) ----
dbx.getCollection(COLL).drop();

// ---- 2) Creación de la colección con validador (estructura exigida) ----
dbx.createCollection(COLL, {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["nombre", "categoria", "peso_toneladas", "descripcion"],
      properties: {
        nombre: { bsonType: "string", minLength: 1 },
        categoria: { bsonType: "string", minLength: 1 },
        peso_toneladas: { bsonType: "number", minimum: 0 },
        descripcion: { bsonType: "string", minLength: 1 }
      }
    }
  }
});
print("OK: colección automoviles.vehiculos creada con validador");

// ---- 3) Seed: los 10 vehículos de la imagen de referencia ----
dbx.getCollection(COLL).insertMany([
  { nombre: "Automóvil",   categoria: "Terrestre (motorizado)",    peso_toneladas: 1.5,   descripcion: "Vehículo común para transporte personal." },
  { nombre: "Motocicleta", categoria: "Terrestre (motorizado)",    peso_toneladas: 0.2,   descripcion: "Vehículo de dos ruedas impulsado por motor." },
  { nombre: "Camión",      categoria: "Terrestre (motorizado)",    peso_toneladas: 10,    descripcion: "Vehículo grande para carga pesada." },
  { nombre: "Bicicleta",   categoria: "Terrestre (no motorizado)", peso_toneladas: 0.015, descripcion: "Vehículo de dos ruedas impulsado por pedales." },
  { nombre: "Monopatín",   categoria: "Terrestre (no motorizado)", peso_toneladas: 0.005, descripcion: "Tabla con ruedas impulsada por el usuario." },
  { nombre: "Barco",       categoria: "Acuático",                  peso_toneladas: 500,   descripcion: "Embarcación grande usada para transporte marítimo." },
  { nombre: "Lancha",      categoria: "Acuático",                  peso_toneladas: 2,     descripcion: "Embarcación pequeña usada en ríos o mares." },
  { nombre: "Avión",       categoria: "Aéreo",                     peso_toneladas: 70,    descripcion: "Aeronave comercial para transporte de pasajeros." },
  { nombre: "Helicóptero", categoria: "Aéreo",                     peso_toneladas: 3,     descripcion: "Aeronave de despegue vertical con rotores." },
  { nombre: "Cohete",      categoria: "Espacial",                 peso_toneladas: 500,   descripcion: "Vehículo propulsado para viajes espaciales." }
]);
print("OK: 10 vehículos insertados");

// ---- 4) Índice único sobre el campo de búsqueda (clave de caché) ----
dbx.getCollection(COLL).createIndex({ nombre: 1 }, { unique: true });
print("OK: índice único { nombre: 1 } creado");

// ---- 5) Verificación final ----
print("Total documentos: " + dbx.getCollection(COLL).countDocuments());
printjson(dbx.getCollection(COLL).findOne({ nombre: "Avión" }, { _id: 0 }));
