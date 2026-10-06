from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
import os
import json
from typing import Dict, List

from . import models, auth, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Luma-like Event Platform")
templates = Jinja2Templates(directory="fastapi_app/templates")

class ConnectionManager:
    def __init__(self):
        # event_id -> list of websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, event_id: int):
        await websocket.accept()
        if event_id not in self.active_connections:
            self.active_connections[event_id] = []
        self.active_connections[event_id].append(websocket)

    def disconnect(self, websocket: WebSocket, event_id: int):
        if event_id in self.active_connections:
            self.active_connections[event_id].remove(websocket)

    async def broadcast(self, event_id: int, message: dict):
        if event_id in self.active_connections:
            for connection in self.active_connections[event_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    pass

manager = ConnectionManager()

def get_current_user(request: Request, db: Session = Depends(database.get_db)):
    user_id = auth.get_current_user_from_cookie(request)
    if not user_id:
        return None
    return db.query(models.User).filter(models.User.id == user_id).first()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user(request, db)
    events = db.query(models.Event).all()
    return templates.TemplateResponse(
        request=request, 
        name="home.html", 
        context={"user": user, "events": events}
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, next: str = "/dashboard"):
    return templates.TemplateResponse(request=request, name="login.html", context={"next": next})

@app.post("/login")
def login(response: Response, email: str = Form(...), password: str = Form(...), next: str = Form("/dashboard"), db: Session = Depends(database.get_db)):
    email = email.strip()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return RedirectResponse(url=f"/login?error=1&next={next}", status_code=status.HTTP_303_SEE_OTHER)
    
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(url=next, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite='lax', max_age=86400)
    return response

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.post("/register")
def register(response: Response, name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    email = email.strip()
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return RedirectResponse(url="/register?error=1", status_code=status.HTTP_303_SEE_OTHER)
        
    hashed = auth.get_password_hash(password)
    user = models.User(name=name, email=email, hashed_password=hashed, role="student")
    db.add(user)
    db.commit()
    
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite='lax', max_age=86400)
    return response

@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@app.get("/event/{event_id}", response_class=HTMLResponse)
def event_detail(request: Request, event_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user(request, db)
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    registered = False
    if user:
        registered = db.query(models.Registration).filter(
            models.Registration.event_id == event_id,
            models.Registration.user_id == user.id
        ).first() is not None
        
    spots_filled = db.query(models.Registration).filter(models.Registration.event_id == event_id).count()
    
    return templates.TemplateResponse(
        request=request,
        name="event.html", 
        context={
            "user": user, 
            "event": event,
            "registered": registered,
            "spots_filled": spots_filled
        }
    )

@app.websocket("/ws/event/{event_id}")
async def websocket_event(websocket: WebSocket, event_id: int):
    await manager.connect(websocket, event_id)
    try:
        while True:
            # We just keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, event_id)

@app.post("/event/{event_id}/register")
async def register_event(
    request: Request, 
    event_id: int, 
    phone: str = Form(None),
    dietary: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(database.get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url=f"/login?next=/event/{event_id}", status_code=status.HTTP_303_SEE_OTHER)
        
    existing = db.query(models.Registration).filter(
        models.Registration.event_id == event_id,
        models.Registration.user_id == user.id
    ).first()
    
    if not existing:
        event = db.query(models.Event).filter(models.Event.id == event_id).first()
        if not event:
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
            
        spots_filled = db.query(models.Registration).filter(
            models.Registration.event_id == event_id, 
            models.Registration.status == "registered"
        ).count()
        
        reg_status = "registered"
        if spots_filled >= event.capacity:
            if event.waitlist_enabled:
                reg_status = "waitlisted"
            else:
                return RedirectResponse(url=f"/event/{event_id}?error=full", status_code=status.HTTP_303_SEE_OTHER)
                
        reg = models.Registration(
            event_id=event_id, 
            user_id=user.id, 
            status=reg_status,
            phone=phone,
            dietary=dietary,
            notes=notes
        )
        db.add(reg)
        db.commit()
        
        # Broadcast real-time update
        new_spots_filled = db.query(models.Registration).filter(
            models.Registration.event_id == event_id, 
            models.Registration.status == "registered"
        ).count()
        await manager.broadcast(event_id, {
            "type": "capacity_update",
            "spots_filled": new_spots_filled,
            "capacity": event.capacity
        })
        
    return RedirectResponse(url=f"/event/{event_id}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/event/create")
def create_event(
    request: Request, 
    title: str = Form(...), 
    description: str = Form(...), 
    category: str = Form(...), 
    venue: str = Form(...), 
    capacity: int = Form(...),
    db: Session = Depends(database.get_db)
):
    user = get_current_user(request, db)
    if not user or user.role not in ["organizer", "admin"]:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    new_event = models.Event(
        title=title,
        description=description,
        category=category,
        venue=venue,
        capacity=capacity,
        organizer_id=user.id,
        status="pending"
    )
    db.add(new_event)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/event/{event_id}/approve")
def approve_event(request: Request, event_id: int, db: Session = Depends(database.get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["faculty", "admin"]:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if event and event.status == "pending":
        event.status = "active"
        db.commit()
        
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/event/{event_id}/attendance/{reg_id}")
def mark_attendance(request: Request, event_id: int, reg_id: int, present: str = Form(...), db: Session = Depends(database.get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in ["organizer", "admin"]:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    reg = db.query(models.Registration).filter(
        models.Registration.id == reg_id, 
        models.Registration.event_id == event_id
    ).first()
    
    if reg and reg.event.organizer_id == user.id:
        reg.present = (present == "true")
        db.commit()
        
    return RedirectResponse(url=f"/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(database.get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login?next=/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        
    registrations = db.query(models.Registration).filter(models.Registration.user_id == user.id).all()
    my_events = db.query(models.Event).filter(models.Event.organizer_id == user.id).all() if user.role in ['organizer', 'admin'] else []
    pending_events = db.query(models.Event).filter(models.Event.status == "pending").all() if user.role in ['faculty', 'admin'] else []
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html", 
        context={
            "user": user, 
            "registrations": registrations,
            "my_events": my_events,
            "pending_events": pending_events
        }
    )
