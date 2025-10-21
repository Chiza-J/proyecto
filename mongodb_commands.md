# Comandos Útiles de MongoDB para TechAssist

## Conectarse a MongoDB
```bash
mongosh
use soporte_ti_db
```

## Ver todas las colecciones
```javascript
show collections
```

## Contar documentos
```javascript
db.users.countDocuments()
db.tickets.countDocuments()
db.comments.countDocuments()
```

## Ver todos los usuarios
```javascript
db.users.find().pretty()
```

## Ver usuarios por rol
```javascript
// Clientes
db.users.find({ role: "cliente" }).pretty()

// Técnicos
db.users.find({ role: "tecnico" }).pretty()

// Administradores
db.users.find({ role: "admin" }).pretty()
```

## Ver todos los tickets
```javascript
db.tickets.find().pretty()
```

## Tickets por estado
```javascript
// Tickets abiertos
db.tickets.find({ status: "abierto" }).pretty()

// Tickets en proceso
db.tickets.find({ status: "en_proceso" }).pretty()

// Tickets cerrados
db.tickets.find({ status: "cerrado" }).pretty()
```

## Tickets por prioridad
```javascript
// Alta prioridad
db.tickets.find({ priority: "alta" }).pretty()

// Media prioridad
db.tickets.find({ priority: "media" }).pretty()

// Baja prioridad
db.tickets.find({ priority: "baja" }).pretty()
```

## Tickets de un cliente específico
```javascript
// Reemplaza USER_ID con el ID del cliente
db.tickets.find({ user_id: "USER_ID" }).pretty()
```

## Tickets asignados a un técnico
```javascript
// Reemplaza TECH_ID con el ID del técnico
db.tickets.find({ technician_id: "TECH_ID" }).pretty()
```

## Ver comentarios de un ticket
```javascript
// Reemplaza TICKET_ID con el ID del ticket
db.comments.find({ ticket_id: "TICKET_ID" }).sort({ created_at: 1 }).pretty()
```

## Ver historial de un ticket
```javascript
// Reemplaza TICKET_ID con el ID del ticket
db.ticket_history.find({ ticket_id: "TICKET_ID" }).sort({ timestamp: -1 }).pretty()
```

## Ver adjuntos de un ticket
```javascript
// Reemplaza TICKET_ID con el ID del ticket
// Nota: no usar .pretty() porque el base64 es muy largo
db.attachments.find({ ticket_id: "TICKET_ID" }, { file_data: 0 })
```

## Buscar usuarios por email
```javascript
db.users.find({ email: "cliente1@empresa.com" }).pretty()
```

## Actualizar estado de un ticket
```javascript
db.tickets.updateOne(
    { id: "TICKET_ID" },
    { 
        $set: { 
            status: "cerrado",
            closed_at: new Date().toISOString()
        }
    }
)
```

## Actualizar prioridad de un ticket
```javascript
db.tickets.updateOne(
    { id: "TICKET_ID" },
    { 
        $set: { 
            priority: "alta",
            last_priority_change: new Date().toISOString()
        }
    }
)
```

## Asignar técnico a un ticket
```javascript
db.tickets.updateOne(
    { id: "TICKET_ID" },
    { 
        $set: { 
            technician_id: "TECH_ID",
            assigned_at: new Date().toISOString()
        }
    }
)
```

## Agregar comentario
```javascript
db.comments.insertOne({
    id: UUID(),
    ticket_id: "TICKET_ID",
    user_id: "USER_ID",
    comment: "Esto es un comentario de prueba",
    created_at: new Date().toISOString()
})
```

## Estadísticas agregadas

### Total de tickets por estado
```javascript
db.tickets.aggregate([
    {
        $group: {
            _id: "$status",
            count: { $sum: 1 }
        }
    }
])
```

### Total de tickets por prioridad
```javascript
db.tickets.aggregate([
    {
        $group: {
            _id: "$priority",
            count: { $sum: 1 }
        }
    }
])
```

### Tickets por categoría
```javascript
db.tickets.aggregate([
    {
        $lookup: {
            from: "categories",
            localField: "category_id",
            foreignField: "id",
            as: "category"
        }
    },
    { $unwind: "$category" },
    {
        $group: {
            _id: "$category.name",
            count: { $sum: 1 }
        }
    }
])
```

### Tickets por técnico
```javascript
db.tickets.aggregate([
    {
        $match: { technician_id: { $ne: null } }
    },
    {
        $lookup: {
            from: "users",
            localField: "technician_id",
            foreignField: "id",
            as: "technician"
        }
    },
    { $unwind: "$technician" },
    {
        $group: {
            _id: "$technician.name",
            total_tickets: { $sum: 1 },
            abiertos: {
                $sum: { $cond: [{ $eq: ["$status", "abierto"] }, 1, 0] }
            },
            en_proceso: {
                $sum: { $cond: [{ $eq: ["$status", "en_proceso"] }, 1, 0] }
            },
            cerrados: {
                $sum: { $cond: [{ $eq: ["$status", "cerrado"] }, 1, 0] }
            }
        }
    }
])
```

## Búsqueda de texto
```javascript
// Buscar tickets por palabras clave en título o descripción
db.tickets.find({
    $or: [
        { title: { $regex: "impresora", $options: "i" } },
        { description: { $regex: "impresora", $options: "i" } }
    ]
}).pretty()
```

## Tickets que requieren escalamiento

### Tickets baja > 24 horas
```javascript
const threshold = new Date(Date.now() - 24 * 60 * 60 * 1000);
db.tickets.find({
    status: { $in: ["abierto", "en_proceso"] },
    priority: "baja",
    last_priority_change: { $lt: threshold.toISOString() }
}).pretty()
```

### Tickets media > 48 horas
```javascript
const threshold = new Date(Date.now() - 48 * 60 * 60 * 1000);
db.tickets.find({
    status: { $in: ["abierto", "en_proceso"] },
    priority: "media",
    last_priority_change: { $lt: threshold.toISOString() }
}).pretty()
```

## Crear índices
```javascript
// Índices para users
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "role": 1 })

// Índices para tickets
db.tickets.createIndex({ "user_id": 1 })
db.tickets.createIndex({ "technician_id": 1 })
db.tickets.createIndex({ "status": 1 })
db.tickets.createIndex({ "priority": 1 })
db.tickets.createIndex({ "created_at": -1 })
db.tickets.createIndex({ "last_priority_change": 1 })

// Índices para comments
db.comments.createIndex({ "ticket_id": 1 })
db.comments.createIndex({ "created_at": -1 })

// Índices para ticket_history
db.ticket_history.createIndex({ "ticket_id": 1 })
db.ticket_history.createIndex({ "timestamp": -1 })

// Índices para attachments
db.attachments.createIndex({ "ticket_id": 1 })
```

## Limpiar base de datos
```javascript
// ⚠️ CUIDADO: Esto borra todos los datos
db.users.deleteMany({})
db.user_sessions.deleteMany({})
db.tickets.deleteMany({})
db.comments.deleteMany({})
db.attachments.deleteMany({})
db.ticket_history.deleteMany({})
db.categories.deleteMany({})
db.departments.deleteMany({})
db.equipments.deleteMany({})
```

## Backup y restauración

### Hacer backup
```bash
# Backup completo
mongodump --db soporte_ti_db --out /backup/$(date +%Y%m%d)

# Backup de una colección específica
mongodump --db soporte_ti_db --collection tickets --out /backup/tickets_$(date +%Y%m%d)
```

### Restaurar backup
```bash
# Restaurar completo
mongorestore --db soporte_ti_db /backup/20250120/soporte_ti_db

# Restaurar una colección
mongorestore --db soporte_ti_db --collection tickets /backup/tickets_20250120/soporte_ti_db/tickets.bson
```

## Exportar a JSON
```bash
# Exportar tickets a JSON
mongoexport --db soporte_ti_db --collection tickets --out tickets.json --pretty

# Exportar usuarios a JSON
mongoexport --db soporte_ti_db --collection users --out users.json --pretty
```

## Importar desde JSON
```bash
# Importar tickets
mongoimport --db soporte_ti_db --collection tickets --file tickets.json

# Importar usuarios
mongoimport --db soporte_ti_db --collection users --file users.json
```

## Verificar el tamaño de la base de datos
```javascript
db.stats()
```

## Ver tamaño de cada colección
```javascript
db.users.stats().size
db.tickets.stats().size
db.attachments.stats().size  // Esta será la más grande por los base64
```
