import os
import sys


def is_frozen():
    """True cuando corre empaquetado por PyInstaller."""
    return getattr(sys, "frozen", False)


def resource_dir():
    """Carpeta con los archivos empaquetados (frontend estatico). En dev, la raiz del repo
    (backend/app/paths.py -> backend/app -> backend -> raiz)."""
    if is_frozen():
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def user_data_dir():
    """Carpeta persistente por usuario para la base de datos.
    En Windows: %APPDATA%\\Vitalis. Sobrevive a que se reemplace el .exe con una version nueva.
    En dev, la carpeta backend/ (comportamiento previo)."""
    if is_frozen():
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(base, "Vitalis")
    else:
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(path, exist_ok=True)
    return path
