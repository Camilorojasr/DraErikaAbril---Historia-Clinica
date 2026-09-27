import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base
from app.models import PatientDB
from app.schemas import StateIn, StateOut
from app.paths import resource_dir

Base.metadata.create_all(bind=engine)

STATE_ID = "vitalis-clinical-db-v3"
FRONTEND_PATH = os.path.join(resource_dir(), "vitalis-frontend.html")

app = FastAPI(title="Vitalis API")

cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in cors_origins if o] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/state", response_model=StateOut)
def get_state(db: Session = Depends(get_db)):
    row = db.get(PatientDB, STATE_ID)
    if not row:
        raise HTTPException(status_code=404, detail="No hay estado guardado todavia")
    return row


@app.put("/api/state", response_model=StateOut)
def put_state(payload: StateIn, db: Session = Depends(get_db)):
    row = db.get(PatientDB, STATE_ID)
    if row:
        row.data = payload.data
    else:
        row = PatientDB(id=STATE_ID, data=payload.data)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/api/state", status_code=204)
def delete_state(db: Session = Depends(get_db)):
    row = db.get(PatientDB, STATE_ID)
    if row:
        db.delete(row)
        db.commit()
    return None


@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_PATH)
