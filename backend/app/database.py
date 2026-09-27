import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.paths import user_data_dir, is_frozen

load_dotenv()

_default_db_path = os.path.join(user_data_dir(), "vitalis.db").replace("\\", "/")
# En el .exe empaquetado ignoramos .env (no viaja con el binario) y usamos
# siempre la carpeta de datos del usuario, para que las actualizaciones del
# .exe no pisen ni pierdan la base de datos existente.
DATABASE_URL = f"sqlite:///{_default_db_path}" if is_frozen() else os.getenv("DATABASE_URL", f"sqlite:///{_default_db_path}")

_is_sqlite = DATABASE_URL.startswith("sqlite")
# timeout (segundos): si otra conexión tiene el archivo bloqueado (p. ej. alguien
# lo abrió con un visor de SQLite para inspeccionarlo), sqlite3 reintenta durante
# este tiempo en vez de fallar de inmediato con "database is locked".
connect_args = {"check_same_thread": False, "timeout": 30} if _is_sqlite else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # WAL: los lectores (p. ej. un visor de SQLite abierto para consultar
        # datos) ya no bloquean al escritor (la app), que es la causa más común
        # de "database is locked" en este tipo de app de un solo archivo.
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
