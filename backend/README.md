# Vitalis backend

Backend FastAPI + SQLAlchemy que reemplaza `localStorage` por persistencia real (Ruta A del handoff: una fila jsonb con el `STATE` completo del frontend).

## Arrancar en desarrollo

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Abre http://127.0.0.1:8000/ — el propio FastAPI sirve `vitalis-frontend.html` como estático (mismo origen, sin problemas de CORS/CSP).

## Base de datos

- Desarrollo: SQLite en `backend/vitalis.db` (se crea sola al arrancar).
- Migraciones con Alembic: `alembic revision --autogenerate -m "mensaje"` y `alembic upgrade head`.
- Para pasar a Postgres en producción: cambia `DATABASE_URL` en `.env` (p. ej. `postgresql://user:pass@host/db`) — SQLAlchemy y Alembic no requieren más cambios de código.

## Endpoints

- `GET /api/state` — devuelve `{data, updated_at}` o 404 si no hay nada guardado.
- `PUT /api/state` — recibe `{data: {...}}` y guarda/actualiza el STATE completo.
- `DELETE /api/state` — borra el estado guardado.

## Próximos pasos (Ruta B, opcional)

Migrar entidad por entidad (pacientes, antecedentes, labs, consultas, etc.) a tablas relacionales y endpoints CRUD propios, según el esquema en `vitalis-backend-handoff.md`, sección 4-5.

## App portable (.exe) para otro computador

Para que alguien más use Vitalis en su propio computador, con su propia base de datos local (independiente de la tuya), sin instalar Python ni nada:

```powershell
cd backend
.\build_exe.ps1
```

Esto genera `dist\Vitalis.exe` — un único archivo (~18 MB). Cópialo (USB, correo, Drive) al otro computador y ejecútalo con doble clic:

- Arranca su propio servidor en `http://127.0.0.1:8794/` y abre el navegador automáticamente.
- Su base de datos vive en `%APPDATA%\Vitalis\vitalis.db` en **ese** computador — no se comparte ni se sincroniza con la tuya.
- Cerrar la ventana de consola apaga el servidor (queda un aviso en pantalla para no cerrarla por accidente).
- No requiere permisos de administrador ni instalar nada más.

**Actualizaciones:** cuando hagas cambios al código, corre `build_exe.ps1` de nuevo y manda el `Vitalis.exe` nuevo — como la base de datos vive en `%APPDATA%`, no en la carpeta del .exe, sus datos existentes no se pierden al reemplazar el archivo.

**Limitación a tener en cuenta:** cada copia (la tuya y la suya) tiene su propia base de datos SQLite independiente — no hay sincronización entre ambas. Si en algún momento necesitan ver y editar exactamente los mismos pacientes desde las dos computadoras, la solución es un servidor compartido en la red o en la nube, no esta versión portable.
