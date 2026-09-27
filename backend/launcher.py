"""Punto de entrada del ejecutable portable de Vitalis.

Arranca el servidor en localhost, abre el navegador automaticamente y
mantiene la consola abierta para que la persona sepa que la app sigue
corriendo (cerrar la ventana apaga el servidor).
"""
import socket
import threading
import time
import webbrowser

import uvicorn

from app.main import app
from app.database import DATABASE_URL

HOST = "127.0.0.1"
PORT = 8794


def port_is_free(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) != 0


def open_browser_when_ready():
    for _ in range(60):
        if not port_is_free(HOST, PORT):
            webbrowser.open(f"http://{HOST}:{PORT}/")
            return
        time.sleep(0.5)


if __name__ == "__main__":
    print("=" * 60)
    print(" Vitalis - Historia clinica")
    print("=" * 60)
    print(f" Base de datos: {DATABASE_URL}")
    print(f" Abriendo en el navegador: http://{HOST}:{PORT}/")
    print(" No cierres esta ventana mientras uses la aplicacion.")
    print("=" * 60)

    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
