# Base de Datos MongoDB - TechAssist

## Configuración de Conexión

```python
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "soporte_ti_db"

from motor.motor_asyncio import AsyncIOMotorClient
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
```

## Colecciones (Collections)

### 1. users
**Descripción:** Almacena información de todos los usuarios del sistema (clientes, técnicos, administradores)

```javascript
{
  "id": "uuid-string",
  "email": "juan.perez@empresa.com",
  "name": "Juan Pérez",
  "password": "hashed_password_bcrypt",  // Solo para JWT, null para OAuth
  "picture": "https://...",  // URL de foto (opcional, OAuth)
  "role": "cliente",  // valores: cliente, tecnico, admin
  "phone": "555-1234",
  "department_id": "dept-uuid",  // FK a departments
  "status": "activo",  // valores: activo, inactivo
  "created_at": "2025-01-20T10:30:00Z"
}
```

**Índices:**
```javascript
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "role": 1 })
db.users.createIndex({ "department_id": 1 })
```

---

### 2. user_sessions
**Descripción:** Almacena sesiones de Google OAuth

```javascript
{
  "id": "session-uuid",
  "user_id": "user-uuid",  // FK a users
  "session_token": "emergent-session-token-xyz",
  "expires_at": "2025-01-27T10:30:00Z",
  "created_at": "2025-01-20T10:30:00Z"
}
```

**Índices:**
```javascript
db.user_sessions.createIndex({ "session_token": 1 })
db.user_sessions.createIndex({ "user_id": 1 })
db.user_sessions.createIndex({ "expires_at": 1 })
```

---

### 3. departments
**Descripción:** Define las áreas de la empresa

```javascript
{
  "id": "dept-uuid",
  "name": "IT",
  "description": "Departamento de Tecnología de la Información"
}
```

**Datos iniciales:**
```javascript
[
  { "id": "uuid-1", "name": "IT", "description": "Departamento de TI" },
  { "id": "uuid-2", "name": "Ventas", "description": "Departamento de ventas" },
  { "id": "uuid-3", "name": "RRHH", "description": "Recursos Humanos" },
  { "id": "uuid-4", "name": "Finanzas", "description": "Departamento financiero" }
]
```

---

### 4. categories
**Descripción:** Clasifica los tipos de incidencias

```javascript
{
  "id": "cat-uuid",
  "name": "Hardware",
  "description": "Problemas relacionados con hardware"
}
```

**Datos iniciales:**
```javascript
[
  { "id": "uuid-1", "name": "Hardware", "description": "Problemas de hardware" },
  { "id": "uuid-2", "name": "Software", "description": "Problemas de software" },
  { "id": "uuid-3", "name": "Red", "description": "Problemas de red" },
  { "id": "uuid-4", "name": "Acceso", "description": "Problemas de acceso" },
  { "id": "uuid-5", "name": "Otro", "description": "Otros problemas" }
]
```

---

### 5. equipments
**Descripción:** Registra dispositivos tecnológicos

```javascript
{
  "id": "equip-uuid",
  "name": "Laptop Dell Latitude 5420",
  "type": "Laptop",
  "brand": "Dell",
  "model": "Latitude 5420",
  "serial_number": "DELL123456",
  "user_id": "user-uuid",  // FK a users (opcional)
  "department_id": "dept-uuid"  // FK a departments (opcional)
}
```

**Índices:**
```javascript
db.equipments.createIndex({ "user_id": 1 })
db.equipments.createIndex({ "department_id": 1 })
db.equipments.createIndex({ "serial_number": 1 })
```

---

### 6. tickets
**Descripción:** Tabla principal - almacena todos los tickets de soporte

```javascript
{
  "id": "ticket-uuid",
  "user_id": "user-uuid",  // FK a users (cliente que crea el ticket)
  "technician_id": "tech-uuid",  // FK a users (técnico asignado, opcional)
  "equipment_id": "equip-uuid",  // FK a equipments (opcional)
  "category_id": "cat-uuid",  // FK a categories
  "title": "Mi computadora no enciende",
  "description": "La laptop Dell no responde al presionar el botón de encendido. La luz indicadora parpadea naranja.",
  "priority": "baja",  // valores: baja, media, alta
  "status": "abierto",  // valores: abierto, en_proceso, cerrado
  "created_at": "2025-01-20T10:30:00Z",
  "assigned_at": "2025-01-20T11:00:00Z",  // Cuando se asigna técnico
  "closed_at": null,  // Cuando se cierra el ticket
  "last_priority_change": "2025-01-20T10:30:00Z"  // Última vez que cambió la prioridad
}
```

**Índices:**
```javascript
db.tickets.createIndex({ "user_id": 1 })
db.tickets.createIndex({ "technician_id": 1 })
db.tickets.createIndex({ "status": 1 })
db.tickets.createIndex({ "priority": 1 })
db.tickets.createIndex({ "category_id": 1 })
db.tickets.createIndex({ "created_at": -1 })
db.tickets.createIndex({ "last_priority_change": 1 })
```

---

### 7. comments
**Descripción:** Historial de comunicación en cada ticket

```javascript
{
  "id": "comment-uuid",
  "ticket_id": "ticket-uuid",  // FK a tickets
  "user_id": "user-uuid",  // FK a users (quien escribe el comentario)
  "comment": "He revisado el equipo y parece ser un problema de la fuente de poder.",
  "created_at": "2025-01-20T14:30:00Z"
}
```

**Índices:**
```javascript
db.comments.createIndex({ "ticket_id": 1 })
db.comments.createIndex({ "user_id": 1 })
db.comments.createIndex({ "created_at": -1 })
```

---

### 8. attachments
**Descripción:** Archivos adjuntos (imágenes en Base64)

```javascript
{
  "id": "attach-uuid",
  "ticket_id": "ticket-uuid",  // FK a tickets
  "filename": "laptop_error_screen.jpg",
  "file_data": "/9j/4AAQSkZJRgABAQEAYABgAAD...",  // Base64 string
  "uploaded_at": "2025-01-20T10:32:00Z"
}
```

**Índices:**
```javascript
db.attachments.createIndex({ "ticket_id": 1 })
```

---

### 9. ticket_history
**Descripción:** Registra todos los cambios realizados en un ticket

```javascript
{
  "id": "history-uuid",
  "ticket_id": "ticket-uuid",  // FK a tickets
  "user_id": "user-uuid",  // FK a users (quien realizó la acción) o "system"
  "action": "Ticket creado con prioridad baja",
  "timestamp": "2025-01-20T10:30:00Z"
}
```

**Ejemplos de acciones:**
- "Ticket creado con prioridad baja"
- "Estado cambiado a en_proceso"
- "Prioridad cambiada de baja a media"
- "Asignado a técnico Juan Pérez"
- "Comentario agregado"
- "Prioridad escalada automáticamente de baja a media"

**Índices:**
```javascript
db.ticket_history.createIndex({ "ticket_id": 1 })
db.ticket_history.createIndex({ "timestamp": -1 })
```

---

## Ejemplos de Queries

### Crear un nuevo ticket
```python
ticket = {
    "id": str(uuid.uuid4()),
    "user_id": "user-123",
    "title": "Problema con impresora",
    "description": "La impresora no responde",
    "category_id": "cat-hardware",
    "priority": "baja",
    "status": "abierto",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "last_priority_change": datetime.now(timezone.utc).isoformat()
}
await db.tickets.insert_one(ticket)
```

### Obtener todos los tickets de un cliente
```python
tickets = await db.tickets.find(
    {"user_id": "user-123"}, 
    {"_id": 0}
).to_list(1000)
```

### Obtener tickets por técnico
```python
tickets = await db.tickets.find(
    {"technician_id": "tech-456"}, 
    {"_id": 0}
).to_list(1000)
```

### Actualizar prioridad de ticket
```python
await db.tickets.update_one(
    {"id": "ticket-789"},
    {
        "$set": {
            "priority": "alta",
            "last_priority_change": datetime.now(timezone.utc).isoformat()
        }
    }
)
```

### Buscar tickets que necesitan escalamiento
```python
from datetime import datetime, timezone, timedelta

# Tickets con prioridad baja > 24 horas
threshold_baja = datetime.now(timezone.utc) - timedelta(hours=24)

tickets = await db.tickets.find({
    "status": {"$in": ["abierto", "en_proceso"]},
    "priority": "baja",
    "last_priority_change": {"$lt": threshold_baja.isoformat()}
}, {"_id": 0}).to_list(1000)
```

### Obtener ticket completo con relaciones
```python
# Obtener ticket
ticket = await db.tickets.find_one({"id": "ticket-789"}, {"_id": 0})

# Obtener usuario
user = await db.users.find_one({"id": ticket["user_id"]}, {"_id": 0})

# Obtener técnico (si existe)
if ticket.get("technician_id"):
    tech = await db.users.find_one({"id": ticket["technician_id"]}, {"_id": 0})

# Obtener comentarios
comments = await db.comments.find(
    {"ticket_id": ticket["id"]}, 
    {"_id": 0}
).to_list(1000)

# Obtener adjuntos
attachments = await db.attachments.find(
    {"ticket_id": ticket["id"]}, 
    {"_id": 0}
).to_list(1000)

# Obtener historial
history = await db.ticket_history.find(
    {"ticket_id": ticket["id"]}, 
    {"_id": 0}
).sort("timestamp", -1).to_list(1000)
```

---

## Reglas de Negocio Implementadas

### 1. Escalamiento Automático de Prioridad
El sistema tiene un scheduler (APScheduler) que corre cada hora:

```python
# Baja → Media después de 24 horas
if ticket.priority == "baja" and hours_passed >= 24:
    new_priority = "media"

# Media → Alta después de 48 horas
elif ticket.priority == "media" and hours_passed >= 48:
    new_priority = "alta"
```

### 2. Control de Acceso por Rol
- **Cliente**: Solo ve sus propios tickets
- **Técnico**: Ve todos los tickets, puede filtrar asignados/resueltos
- **Admin**: Acceso completo

### 3. Historial Automático
Cada acción genera una entrada en `ticket_history`:
- Creación de ticket
- Cambio de estado
- Cambio de prioridad
- Asignación de técnico
- Comentarios agregados
- Escalamiento automático

---

## Scripts de Inicialización

### Seed inicial de datos (ejecutado en startup)
```python
@app.on_event("startup")
async def seed_initial_data():
    # Categorías
    cat_count = await db.categories.count_documents({})
    if cat_count == 0:
        categories = [
            {"id": str(uuid.uuid4()), "name": "Hardware", "description": "Problemas de hardware"},
            {"id": str(uuid.uuid4()), "name": "Software", "description": "Problemas de software"},
            {"id": str(uuid.uuid4()), "name": "Red", "description": "Problemas de red"},
            {"id": str(uuid.uuid4()), "name": "Acceso", "description": "Problemas de acceso"},
            {"id": str(uuid.uuid4()), "name": "Otro", "description": "Otros problemas"}
        ]
        await db.categories.insert_many(categories)
    
    # Departamentos
    dept_count = await db.departments.count_documents({})
    if dept_count == 0:
        departments = [
            {"id": str(uuid.uuid4()), "name": "IT", "description": "Departamento de TI"},
            {"id": str(uuid.uuid4()), "name": "Ventas", "description": "Departamento de ventas"},
            {"id": str(uuid.uuid4()), "name": "RRHH", "description": "Recursos Humanos"},
            {"id": str(uuid.uuid4()), "name": "Finanzas", "description": "Departamento financiero"}
        ]
        await db.departments.insert_many(departments)
```

---

## Backup y Restauración

### Backup de la base de datos
```bash
mongodump --db soporte_ti_db --out /backup/$(date +%Y%m%d)
```

### Restauración
```bash
mongorestore --db soporte_ti_db /backup/20250120/soporte_ti_db
```

---

## Notas Importantes

1. **UUIDs**: Todos los IDs son UUID v4 generados en Python
2. **Timestamps**: Todos en formato ISO 8601 con timezone UTC
3. **Passwords**: Hasheados con bcrypt (salt rounds = 12)
4. **Base64**: Las imágenes se almacenan como strings base64
5. **Relaciones**: No hay foreign keys nativos, se manejan en la aplicación
6. **_id de MongoDB**: Se usa el campo `id` para queries, `_id` es ignorado
