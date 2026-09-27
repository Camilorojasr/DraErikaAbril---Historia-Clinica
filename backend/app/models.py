from sqlalchemy import Column, String, JSON, DateTime, func
from app.database import Base


class PatientDB(Base):
    """Ruta A: todo el STATE del frontend serializado en una sola fila jsonb."""
    __tablename__ = "patient_db"

    id = Column(String, primary_key=True)
    data = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
