from fastapi import FastAPI, APIRouter, HTTPException, Depends, Response, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from apscheduler.schedulers.background import BackgroundScheduler
import requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

security = HTTPBearer(auto_error=False)

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 48

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ============= MODELS =============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    email: str
    name: str
    password: Optional[str] = None
    picture: Optional[str] = None
    role: str  # cliente, tecnico, admin
    phone: Optional[str] = None
    department_id: Optional[str] = None
    status: str = "activo"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Department(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None

class Equipment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    user_id: Optional[str] = None
    department_id: Optional[str] = None

class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None

class Priority(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # baja, media, alta
    response_time_hours: int
    color: str

class TicketStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # abierto, en_proceso, cerrado
    description: Optional[str] = None

class Ticket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    technician_id: Optional[str] = None
    equipment_id: Optional[str] = None
    category_id: str
    title: str
    description: str
    priority: str  # baja, media, alta
    status: str  # abierto, en_proceso, cerrado
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assigned_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    last_priority_change: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    user_id: str
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Attachment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    filename: str
    file_data: str  # base64
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TicketHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    user_id: str
    action: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============= INPUT MODELS =============

class RegisterInput(BaseModel):
    email: str
    name: str
    password: str
    role: str = "cliente"
    phone: Optional[str] = None
    department_id: Optional[str] = None

class LoginInput(BaseModel):
    email: str
    password: str

class CreateTicketInput(BaseModel):
    title: str
    description: str
    category_id: str
    equipment_id: Optional[str] = None
    attachments: Optional[List[dict]] = []  # [{filename, file_data}]

class UpdateTicketInput(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    technician_id: Optional[str] = None

class CreateCommentInput(BaseModel):
    comment: str

class CreateDepartmentInput(BaseModel):
    name: str
    description: Optional[str] = None

class CreateCategoryInput(BaseModel):
    name: str
    description: Optional[str] = None

class CreateEquipmentInput(BaseModel):
    name: str
    type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    user_id: Optional[str] = None
    department_id: Optional[str] = None

# ============= AUTH HELPERS =============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    # Check cookie first
    session_token = request.cookies.get('session_token')
    
    # Fallback to Authorization header
    if not session_token and credentials:
        session_token = credentials.credentials
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if it's JWT token
    try:
        payload = jwt.decode(session_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_doc = await db.users.find_one({"id": payload['user_id']}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        user_doc.pop('password', None)
        return User(**user_doc)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        pass
    
    # Check if it's Google OAuth session token
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    session = UserSession(**session_doc)
    if session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"id": session.user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    user_doc.pop('password', None)
    return User(**user_doc)

# ============= AUTH ENDPOINTS =============

@api_router.post("/auth/register")
async def register(input: RegisterInput):
    # Check if user exists
    existing = await db.users.find_one({"email": input.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=input.email,
        name=input.name,
        password=hash_password(input.password),
        role=input.role,
        phone=input.phone,
        department_id=input.department_id
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Create JWT token
    token = create_jwt_token(user.id, user.email, user.role)
    
    user_dict = user.model_dump()
    user_dict.pop('password', None)
    
    return {"user": user_dict, "token": token}

@api_router.post("/auth/login")
async def login(input: LoginInput):
    user_doc = await db.users.find_one({"email": input.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**user_doc)
    if not user.password or not verify_password(input.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user.id, user.email, user.role)
    
    user_dict = user.model_dump()
    user_dict.pop('password', None)
    
    return {"user": user_dict, "token": token}

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    user_dict = current_user.model_dump()
    user_dict.pop('password', None)
    return user_dict

@api_router.get("/auth/google")
async def google_auth(redirect_url: str):
    auth_url = f"https://auth.emergentagent.com/?redirect={redirect_url}"
    return {"auth_url": auth_url}

@api_router.post("/auth/session")
async def create_session_from_google(session_id: str, response: Response):
    # Get user data from Emergent auth
    headers = {"X-Session-ID": session_id}
    resp = requests.get("https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data", headers=headers)
    
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    
    data = resp.json()
    
    # Check if user exists
    user_doc = await db.users.find_one({"email": data['email']}, {"_id": 0})
    
    if not user_doc:
        # Create new user
        user = User(
            email=data['email'],
            name=data['name'],
            picture=data.get('picture'),
            role='cliente',
            status='activo'
        )
        doc = user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
    else:
        user = User(**user_doc)
    
    # Create session
    session = UserSession(
        user_id=user.id,
        session_token=data['session_token'],
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    
    session_doc = session.model_dump()
    session_doc['created_at'] = session_doc['created_at'].isoformat()
    session_doc['expires_at'] = session_doc['expires_at'].isoformat()
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=data['session_token'],
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    user_dict = user.model_dump()
    user_dict.pop('password', None)
    
    return {"user": user_dict, "session_token": data['session_token']}

@api_router.post("/auth/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    # Delete session from database
    await db.user_sessions.delete_many({"user_id": current_user.id})
    
    # Clear cookie
    response.delete_cookie("session_token")
    
    return {"message": "Logged out successfully"}

# ============= TICKET ENDPOINTS =============

@api_router.post("/tickets", response_model=Ticket)
async def create_ticket(input: CreateTicketInput, current_user: User = Depends(get_current_user)):
    ticket = Ticket(
        user_id=current_user.id,
        title=input.title,
        description=input.description,
        category_id=input.category_id,
        equipment_id=input.equipment_id,
        priority="baja",
        status="abierto"
    )
    
    doc = ticket.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['last_priority_change'] = doc['last_priority_change'].isoformat()
    await db.tickets.insert_one(doc)
    
    # Save attachments
    if input.attachments:
        for att in input.attachments:
            attachment = Attachment(
                ticket_id=ticket.id,
                filename=att['filename'],
                file_data=att['file_data']
            )
            att_doc = attachment.model_dump()
            att_doc['uploaded_at'] = att_doc['uploaded_at'].isoformat()
            await db.attachments.insert_one(att_doc)
    
    # Create history
    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=current_user.id,
        action=f"Ticket creado con prioridad {ticket.priority}"
    )
    hist_doc = history.model_dump()
    hist_doc['timestamp'] = hist_doc['timestamp'].isoformat()
    await db.ticket_history.insert_one(hist_doc)
    
    return ticket

@api_router.get("/tickets")
async def get_tickets(current_user: User = Depends(get_current_user)):
    if current_user.role == "cliente":
        # Clientes solo ven sus tickets
        tickets = await db.tickets.find({"user_id": current_user.id}, {"_id": 0}).to_list(1000)
    else:
        # Técnicos y admins ven todos
        tickets = await db.tickets.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO strings to datetime
    for ticket in tickets:
        if isinstance(ticket.get('created_at'), str):
            ticket['created_at'] = datetime.fromisoformat(ticket['created_at'])
        if isinstance(ticket.get('last_priority_change'), str):
            ticket['last_priority_change'] = datetime.fromisoformat(ticket['last_priority_change'])
        if ticket.get('assigned_at') and isinstance(ticket['assigned_at'], str):
            ticket['assigned_at'] = datetime.fromisoformat(ticket['assigned_at'])
        if ticket.get('closed_at') and isinstance(ticket['closed_at'], str):
            ticket['closed_at'] = datetime.fromisoformat(ticket['closed_at'])
    
    # Enrich with user and technician names
    for ticket in tickets:
        user = await db.users.find_one({"id": ticket['user_id']}, {"_id": 0, "name": 1})
        ticket['user_name'] = user['name'] if user else "Unknown"
        
        if ticket.get('technician_id'):
            tech = await db.users.find_one({"id": ticket['technician_id']}, {"_id": 0, "name": 1})
            ticket['technician_name'] = tech['name'] if tech else "Unknown"
        else:
            ticket['technician_name'] = None
        
        # Get category name
        category = await db.categories.find_one({"id": ticket['category_id']}, {"_id": 0, "name": 1})
        ticket['category_name'] = category['name'] if category else "Unknown"
    
    return tickets

@api_router.get("/tickets/my-assigned")
async def get_my_assigned_tickets(current_user: User = Depends(get_current_user)):
    if current_user.role == "cliente":
        raise HTTPException(status_code=403, detail="Access denied")
    
    tickets = await db.tickets.find({"technician_id": current_user.id}, {"_id": 0}).to_list(1000)
    
    for ticket in tickets:
        if isinstance(ticket.get('created_at'), str):
            ticket['created_at'] = datetime.fromisoformat(ticket['created_at'])
        if isinstance(ticket.get('last_priority_change'), str):
            ticket['last_priority_change'] = datetime.fromisoformat(ticket['last_priority_change'])
        if ticket.get('assigned_at') and isinstance(ticket['assigned_at'], str):
            ticket['assigned_at'] = datetime.fromisoformat(ticket['assigned_at'])
        if ticket.get('closed_at') and isinstance(ticket['closed_at'], str):
            ticket['closed_at'] = datetime.fromisoformat(ticket['closed_at'])
    
    return tickets

@api_router.get("/tickets/my-resolved")
async def get_my_resolved_tickets(current_user: User = Depends(get_current_user)):
    if current_user.role == "cliente":
        raise HTTPException(status_code=403, detail="Access denied")
    
    tickets = await db.tickets.find({
        "technician_id": current_user.id,
        "status": "cerrado"
    }, {"_id": 0}).to_list(1000)
    
    for ticket in tickets:
        if isinstance(ticket.get('created_at'), str):
            ticket['created_at'] = datetime.fromisoformat(ticket['created_at'])
        if isinstance(ticket.get('last_priority_change'), str):
            ticket['last_priority_change'] = datetime.fromisoformat(ticket['last_priority_change'])
        if ticket.get('assigned_at') and isinstance(ticket['assigned_at'], str):
            ticket['assigned_at'] = datetime.fromisoformat(ticket['assigned_at'])
        if ticket.get('closed_at') and isinstance(ticket['closed_at'], str):
            ticket['closed_at'] = datetime.fromisoformat(ticket['closed_at'])
    
    return tickets

@api_router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, current_user: User = Depends(get_current_user)):
    ticket_doc = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket_doc:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket = Ticket(**ticket_doc)
    
    # Check permissions
    if current_user.role == "cliente" and ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get user info
    user = await db.users.find_one({"id": ticket.user_id}, {"_id": 0})
    ticket_dict = ticket.model_dump()
    ticket_dict['user'] = User(**user).model_dump() if user else None
    
    # Get technician info
    if ticket.technician_id:
        tech = await db.users.find_one({"id": ticket.technician_id}, {"_id": 0})
        ticket_dict['technician'] = User(**tech).model_dump() if tech else None
    
    # Get category
    category = await db.categories.find_one({"id": ticket.category_id}, {"_id": 0})
    ticket_dict['category'] = Category(**category).model_dump() if category else None
    
    # Get equipment
    if ticket.equipment_id:
        equipment = await db.equipments.find_one({"id": ticket.equipment_id}, {"_id": 0})
        ticket_dict['equipment'] = Equipment(**equipment).model_dump() if equipment else None
    
    # Get comments
    comments_docs = await db.comments.find({"ticket_id": ticket_id}, {"_id": 0}).to_list(1000)
    comments = []
    for comment_doc in comments_docs:
        if isinstance(comment_doc.get('created_at'), str):
            comment_doc['created_at'] = datetime.fromisoformat(comment_doc['created_at'])
        comment = Comment(**comment_doc)
        comment_dict = comment.model_dump()
        user = await db.users.find_one({"id": comment.user_id}, {"_id": 0})
        comment_dict['user_name'] = user['name'] if user else "Unknown"
        comments.append(comment_dict)
    ticket_dict['comments'] = comments
    
    # Get attachments
    attachments_docs = await db.attachments.find({"ticket_id": ticket_id}, {"_id": 0}).to_list(1000)
    attachments = []
    for att_doc in attachments_docs:
        if isinstance(att_doc.get('uploaded_at'), str):
            att_doc['uploaded_at'] = datetime.fromisoformat(att_doc['uploaded_at'])
        attachments.append(Attachment(**att_doc).model_dump())
    ticket_dict['attachments'] = attachments
    
    # Get history
    history_docs = await db.ticket_history.find({"ticket_id": ticket_id}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    history = []
    for hist_doc in history_docs:
        if isinstance(hist_doc.get('timestamp'), str):
            hist_doc['timestamp'] = datetime.fromisoformat(hist_doc['timestamp'])
        hist = TicketHistory(**hist_doc)
        hist_dict = hist.model_dump()
        user = await db.users.find_one({"id": hist.user_id}, {"_id": 0})
        hist_dict['user_name'] = user['name'] if user else "Unknown"
        history.append(hist_dict)
    ticket_dict['history'] = history
    
    return ticket_dict

@api_router.put("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, input: UpdateTicketInput, current_user: User = Depends(get_current_user)):
    ticket_doc = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket_doc:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket = Ticket(**ticket_doc)
    
    # Check permissions
    if current_user.role == "cliente":
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {}
    history_action = []
    
    if input.status:
        update_data['status'] = input.status
        history_action.append(f"Estado cambiado a {input.status}")
        
        if input.status == "cerrado":
            update_data['closed_at'] = datetime.now(timezone.utc).isoformat()
    
    if input.priority:
        old_priority = ticket.priority
        update_data['priority'] = input.priority
        update_data['last_priority_change'] = datetime.now(timezone.utc).isoformat()
        history_action.append(f"Prioridad cambiada de {old_priority} a {input.priority}")
    
    if input.technician_id:
        if not ticket.technician_id:
            update_data['assigned_at'] = datetime.now(timezone.utc).isoformat()
        update_data['technician_id'] = input.technician_id
        tech = await db.users.find_one({"id": input.technician_id}, {"_id": 0})
        tech_name = tech['name'] if tech else "Unknown"
        history_action.append(f"Asignado a técnico {tech_name}")
    
    if update_data:
        await db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
        
        # Add history
        history = TicketHistory(
            ticket_id=ticket_id,
            user_id=current_user.id,
            action=" | ".join(history_action)
        )
        hist_doc = history.model_dump()
        hist_doc['timestamp'] = hist_doc['timestamp'].isoformat()
        await db.ticket_history.insert_one(hist_doc)
    
    # Get updated ticket
    updated_ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if isinstance(updated_ticket.get('created_at'), str):
        updated_ticket['created_at'] = datetime.fromisoformat(updated_ticket['created_at'])
    if isinstance(updated_ticket.get('last_priority_change'), str):
        updated_ticket['last_priority_change'] = datetime.fromisoformat(updated_ticket['last_priority_change'])
    if updated_ticket.get('assigned_at') and isinstance(updated_ticket['assigned_at'], str):
        updated_ticket['assigned_at'] = datetime.fromisoformat(updated_ticket['assigned_at'])
    if updated_ticket.get('closed_at') and isinstance(updated_ticket['closed_at'], str):
        updated_ticket['closed_at'] = datetime.fromisoformat(updated_ticket['closed_at'])
    
    return Ticket(**updated_ticket)

@api_router.delete("/tickets/{ticket_id}")
async def delete_ticket(ticket_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete tickets")
    
    result = await db.tickets.delete_one({"id": ticket_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Delete related data
    await db.comments.delete_many({"ticket_id": ticket_id})
    await db.attachments.delete_many({"ticket_id": ticket_id})
    await db.ticket_history.delete_many({"ticket_id": ticket_id})
    
    return {"message": "Ticket deleted successfully"}

# ============= COMMENT ENDPOINTS =============

@api_router.post("/tickets/{ticket_id}/comments")
async def create_comment(ticket_id: str, input: CreateCommentInput, current_user: User = Depends(get_current_user)):
    # Check ticket exists
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    comment = Comment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        comment=input.comment
    )
    
    doc = comment.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.comments.insert_one(doc)
    
    # Add to history
    history = TicketHistory(
        ticket_id=ticket_id,
        user_id=current_user.id,
        action="Comentario agregado"
    )
    hist_doc = history.model_dump()
    hist_doc['timestamp'] = hist_doc['timestamp'].isoformat()
    await db.ticket_history.insert_one(hist_doc)
    
    return comment

# ============= ATTACHMENT ENDPOINTS =============

@api_router.post("/tickets/{ticket_id}/attachments")
async def add_attachment(ticket_id: str, filename: str, file_data: str, current_user: User = Depends(get_current_user)):
    # Check ticket exists
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    attachment = Attachment(
        ticket_id=ticket_id,
        filename=filename,
        file_data=file_data
    )
    
    doc = attachment.model_dump()
    doc['uploaded_at'] = doc['uploaded_at'].isoformat()
    await db.attachments.insert_one(doc)
    
    return attachment

# ============= DEPARTMENT ENDPOINTS =============

@api_router.post("/departments")
async def create_department(input: CreateDepartmentInput, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create departments")
    
    department = Department(name=input.name, description=input.description)
    await db.departments.insert_one(department.model_dump())
    return department

@api_router.get("/departments")
async def get_departments():
    departments = await db.departments.find({}, {"_id": 0}).to_list(1000)
    return departments

# ============= CATEGORY ENDPOINTS =============

@api_router.post("/categories")
async def create_category(input: CreateCategoryInput, current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create categories")
    
    category = Category(name=input.name, description=input.description)
    await db.categories.insert_one(category.model_dump())
    return category

@api_router.get("/categories")
async def get_categories():
    categories = await db.categories.find({}, {"_id": 0}).to_list(1000)
    return categories

# ============= EQUIPMENT ENDPOINTS =============

@api_router.post("/equipments")
async def create_equipment(input: CreateEquipmentInput, current_user: User = Depends(get_current_user)):
    equipment = Equipment(
        name=input.name,
        type=input.type,
        brand=input.brand,
        model=input.model,
        serial_number=input.serial_number,
        user_id=input.user_id,
        department_id=input.department_id
    )
    await db.equipments.insert_one(equipment.model_dump())
    return equipment

@api_router.get("/equipments")
async def get_equipments(current_user: User = Depends(get_current_user)):
    equipments = await db.equipments.find({}, {"_id": 0}).to_list(1000)
    return equipments

# ============= USERS ENDPOINTS =============

@api_router.get("/users")
async def get_users(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "tecnico"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.get("/users/technicians")
async def get_technicians(current_user: User = Depends(get_current_user)):
    technicians = await db.users.find({"role": "tecnico"}, {"_id": 0, "password": 0}).to_list(1000)
    return technicians

# ============= PRIORITY ESCALATION TASK =============

async def escalate_ticket_priorities():
    """Background task to escalate ticket priorities"""
    try:
        now = datetime.now(timezone.utc)
        
        # Get all open and in-process tickets
        tickets = await db.tickets.find({
            "status": {"$in": ["abierto", "en_proceso"]}
        }, {"_id": 0}).to_list(10000)
        
        for ticket_doc in tickets:
            ticket = Ticket(**ticket_doc)
            
            # Parse last_priority_change if it's a string
            if isinstance(ticket.last_priority_change, str):
                ticket.last_priority_change = datetime.fromisoformat(ticket.last_priority_change)
            
            time_diff = now - ticket.last_priority_change
            hours_passed = time_diff.total_seconds() / 3600
            
            should_update = False
            new_priority = None
            
            # Baja -> Media after 24 hours
            if ticket.priority == "baja" and hours_passed >= 24:
                new_priority = "media"
                should_update = True
            
            # Media -> Alta after 48 hours
            elif ticket.priority == "media" and hours_passed >= 48:
                new_priority = "alta"
                should_update = True
            
            if should_update:
                await db.tickets.update_one(
                    {"id": ticket.id},
                    {
                        "$set": {
                            "priority": new_priority,
                            "last_priority_change": now.isoformat()
                        }
                    }
                )
                
                # Add history
                history = TicketHistory(
                    ticket_id=ticket.id,
                    user_id="system",
                    action=f"Prioridad escalada automáticamente de {ticket.priority} a {new_priority}"
                )
                hist_doc = history.model_dump()
                hist_doc['timestamp'] = hist_doc['timestamp'].isoformat()
                await db.ticket_history.insert_one(hist_doc)
                
                logging.info(f"Ticket {ticket.id} escalated from {ticket.priority} to {new_priority}")
        
    except Exception as e:
        logging.error(f"Error in escalate_ticket_priorities: {e}")

def run_escalation_task():
    """Wrapper to run async task in scheduler"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(escalate_ticket_priorities())
    loop.close()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_escalation_task, 'interval', hours=1)
scheduler.start()

# ============= SEED DATA ON STARTUP =============

@app.on_event("startup")
async def seed_initial_data():
    """Seed initial categories and priorities"""
    # Check if categories exist
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
        logging.info("Initial categories seeded")
    
    # Check if departments exist
    dept_count = await db.departments.count_documents({})
    if dept_count == 0:
        departments = [
            {"id": str(uuid.uuid4()), "name": "IT", "description": "Departamento de TI"},
            {"id": str(uuid.uuid4()), "name": "Ventas", "description": "Departamento de ventas"},
            {"id": str(uuid.uuid4()), "name": "RRHH", "description": "Recursos Humanos"},
            {"id": str(uuid.uuid4()), "name": "Finanzas", "description": "Departamento financiero"}
        ]
        await db.departments.insert_many(departments)
        logging.info("Initial departments seeded")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    client.close()

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)