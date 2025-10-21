#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos de ejemplo
Ejecutar: python3 seed_database.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid
import bcrypt

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "soporte_ti_db"

async def seed_database():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("🗑️  Limpiando base de datos...")
    await db.users.delete_many({})
    await db.tickets.delete_many({})
    await db.comments.delete_many({})
    await db.attachments.delete_many({})
    await db.ticket_history.delete_many({})
    await db.categories.delete_many({})
    await db.departments.delete_many({})
    await db.equipments.delete_many({})
    
    # 1. Departamentos
    print("📁 Creando departamentos...")
    departments = [
        {"id": str(uuid.uuid4()), "name": "IT", "description": "Departamento de TI"},
        {"id": str(uuid.uuid4()), "name": "Ventas", "description": "Departamento de ventas"},
        {"id": str(uuid.uuid4()), "name": "RRHH", "description": "Recursos Humanos"},
        {"id": str(uuid.uuid4()), "name": "Finanzas", "description": "Departamento financiero"}
    ]
    await db.departments.insert_many(departments)
    dept_it_id = departments[0]["id"]
    
    # 2. Categorías
    print("🏷️  Creando categorías...")
    categories = [
        {"id": str(uuid.uuid4()), "name": "Hardware", "description": "Problemas de hardware"},
        {"id": str(uuid.uuid4()), "name": "Software", "description": "Problemas de software"},
        {"id": str(uuid.uuid4()), "name": "Red", "description": "Problemas de red"},
        {"id": str(uuid.uuid4()), "name": "Acceso", "description": "Problemas de acceso"},
        {"id": str(uuid.uuid4()), "name": "Otro", "description": "Otros problemas"}
    ]
    await db.categories.insert_many(categories)
    cat_hardware_id = categories[0]["id"]
    cat_software_id = categories[1]["id"]
    
    # 3. Usuarios
    print("👥 Creando usuarios...")
    password_hash = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    users = [
        {
            "id": str(uuid.uuid4()),
            "email": "admin@techassist.com",
            "name": "Administrador",
            "password": password_hash,
            "role": "admin",
            "phone": "555-0001",
            "department_id": dept_it_id,
            "status": "activo",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "email": "tecnico1@techassist.com",
            "name": "Carlos Técnico",
            "password": password_hash,
            "role": "tecnico",
            "phone": "555-0002",
            "department_id": dept_it_id,
            "status": "activo",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "email": "tecnico2@techassist.com",
            "name": "María Soporte",
            "password": password_hash,
            "role": "tecnico",
            "phone": "555-0003",
            "department_id": dept_it_id,
            "status": "activo",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "email": "cliente1@empresa.com",
            "name": "Juan Pérez",
            "password": password_hash,
            "role": "cliente",
            "phone": "555-1001",
            "status": "activo",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "email": "cliente2@empresa.com",
            "name": "Ana García",
            "password": password_hash,
            "role": "cliente",
            "phone": "555-1002",
            "status": "activo",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    await db.users.insert_many(users)
    
    cliente1_id = users[3]["id"]
    cliente2_id = users[4]["id"]
    tecnico1_id = users[1]["id"]
    
    # 4. Equipos
    print("💻 Creando equipos...")
    equipments = [
        {
            "id": str(uuid.uuid4()),
            "name": "Laptop Dell Latitude 5420",
            "type": "Laptop",
            "brand": "Dell",
            "model": "Latitude 5420",
            "serial_number": "DELL-001",
            "user_id": cliente1_id,
            "department_id": None
        },
        {
            "id": str(uuid.uuid4()),
            "name": "HP Impresora LaserJet",
            "type": "Impresora",
            "brand": "HP",
            "model": "LaserJet Pro M404dn",
            "serial_number": "HP-002",
            "user_id": None,
            "department_id": dept_it_id
        }
    ]
    await db.equipments.insert_many(equipments)
    laptop_id = equipments[0]["id"]
    
    # 5. Tickets
    print("🎫 Creando tickets...")
    tickets = [
        {
            "id": str(uuid.uuid4()),
            "user_id": cliente1_id,
            "technician_id": tecnico1_id,
            "equipment_id": laptop_id,
            "category_id": cat_hardware_id,
            "title": "Laptop no enciende",
            "description": "Mi laptop Dell no responde al presionar el botón de encendido. La luz LED parpadea en naranja.",
            "priority": "alta",
            "status": "en_proceso",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "closed_at": None,
            "last_priority_change": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": cliente2_id,
            "technician_id": None,
            "equipment_id": None,
            "category_id": cat_software_id,
            "title": "Error al abrir Excel",
            "description": "Cuando intento abrir archivos de Excel me sale un error de 'archivo corrupto'.",
            "priority": "media",
            "status": "abierto",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "assigned_at": None,
            "closed_at": None,
            "last_priority_change": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": cliente1_id,
            "technician_id": tecnico1_id,
            "equipment_id": None,
            "category_id": categories[2]["id"],  # Red
            "title": "Sin acceso a internet",
            "description": "No puedo conectarme a la red WiFi de la oficina.",
            "priority": "baja",
            "status": "cerrado",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "last_priority_change": datetime.now(timezone.utc).isoformat()
        }
    ]
    await db.tickets.insert_many(tickets)
    
    ticket1_id = tickets[0]["id"]
    ticket3_id = tickets[2]["id"]
    
    # 6. Comentarios
    print("💬 Creando comentarios...")
    comments = [
        {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket1_id,
            "user_id": tecnico1_id,
            "comment": "He revisado el equipo. Parece ser un problema con la fuente de poder. Voy a reemplazarla.",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket1_id,
            "user_id": cliente1_id,
            "comment": "Gracias por la actualización. ¿Cuánto tiempo tomará?",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket3_id,
            "user_id": tecnico1_id,
            "comment": "Problema resuelto. El router estaba desconectado.",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    await db.comments.insert_many(comments)
    
    # 7. Historial
    print("📜 Creando historial...")
    history = [
        {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket1_id,
            "user_id": cliente1_id,
            "action": "Ticket creado con prioridad baja",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket1_id,
            "user_id": "system",
            "action": "Prioridad escalada automáticamente de baja a media",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket1_id,
            "user_id": tecnico1_id,
            "action": "Asignado a técnico Carlos Técnico | Estado cambiado a en_proceso | Prioridad cambiada de media a alta",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket3_id,
            "user_id": cliente1_id,
            "action": "Ticket creado con prioridad baja",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "ticket_id": ticket3_id,
            "user_id": tecnico1_id,
            "action": "Estado cambiado a cerrado",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]
    await db.ticket_history.insert_many(history)
    
    print("\n✅ Base de datos poblada exitosamente!")
    print("\n📊 Resumen:")
    print(f"   • {len(departments)} departamentos")
    print(f"   • {len(categories)} categorías")
    print(f"   • {len(users)} usuarios (1 admin, 2 técnicos, 2 clientes)")
    print(f"   • {len(equipments)} equipos")
    print(f"   • {len(tickets)} tickets")
    print(f"   • {len(comments)} comentarios")
    print(f"   • {len(history)} entradas de historial")
    
    print("\n🔐 Credenciales de prueba:")
    print("   Admin:     admin@techassist.com / password123")
    print("   Técnico 1: tecnico1@techassist.com / password123")
    print("   Técnico 2: tecnico2@techassist.com / password123")
    print("   Cliente 1: cliente1@empresa.com / password123")
    print("   Cliente 2: cliente2@empresa.com / password123")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
