// ============================================================
// DB/01_seed_automoviles.js
// Crea la BD `automoviles` y la colección `vehiculos` con los
// 10 documentos de la imagen de referencia.
// Ejecución manual (elige UNA):
//   mongosh --file DB/01_seed_automoviles.js
//   mongosh "mongodb://localhost:27017/automoviles" --file DB/01_seed_automoviles.js
// ============================================================
const DB_NAME = "automoviles";
const COLL = "vehiculos";

db.getSiblingDB(DB_NAME).getCollection(COLL).drop();

const vehiculos = [
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
];

const res = db.getSiblingDB(DB_NAME).getCollection(COLL).insertMany(vehiculos);
print(`OK: insertados ${res.insertedCount} vehículos en ${DB_NAME}.${COLL}`);

// Índice único sobre el campo identificador (el caché usa este campo como clave)
db.getSiblingDB(DB_NAME).getCollection(COLL).createIndex({ nombre: 1 }, { unique: true });
print("OK: índice único { nombre: 1 } creado");

// Verificación rápida
printjson(db.getSiblingDB(DB_NAME).getCollection(COLL).find({}, { _id: 0 }).sort({ nombre: 1 }).toArray());
