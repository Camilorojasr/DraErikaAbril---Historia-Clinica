# Vitalis — Handoff para construir el backend con Claude Code

Este documento resume el estado actual del proyecto y te da todo lo que necesitas para pedirle a Claude Code, en tu máquina, que construya el backend real en **Python/FastAPI + PostgreSQL**. Incluye el modelo de datos, los endpoints, cómo conectar el frontend existente, y un prompt listo para pegar.

## 1. Punto de partida

`vitalis-frontend.html` (adjunto en esta conversación) es el archivo completo de la interfaz actual: HTML + CSS + JavaScript en un solo archivo, sin build step, con una arquitectura en capas ya pensada para esto:

```
UI (render*, event listeners)
  -> Servicios (PatientService, ConsultaService, LabService, ...)
     -> Repo (sabe qué se guarda y bajo qué clave)
        -> StorageAdapter (hoy: LocalStorageAdapter)
```

Todo el estado vive en un único objeto `STATE = { patients: {...}, order: [...] }`. Los servicios mutan ese objeto y llaman a `persist()`, que delega en `Repo.persistAll()` / `Repo.loadAll()`, que a su vez delegan en `StorageAdapter.save(key, value)` / `StorageAdapter.load(key)`. Ese último eslabón es el único que hay que reemplazar para tener persistencia real.

## 2. Algo que necesitas saber antes de empezar (importante)

El HTML que tienes publicado como Artifact en claude.ai **no va a poder hablar directamente con un backend que tú despliegues**. Los artefactos publicados corren con una política de seguridad de contenido que bloquea `fetch`/`XHR`/`WebSocket` hacia cualquier dominio que no esté en una lista blanca muy corta (CDNs de fuentes y librerías, nada de APIs propias). Esto significa que, en cuanto tengas un backend real, el sitio donde vive la interfaz también tiene que mudarse fuera del Artifact: lo más simple es que el propio FastAPI sirva `index.html` como archivo estático (una sola app, un solo dominio, sin problema de CORS ni de CSP), o que lo despliegues por separado (Vercel/Netlify) apuntando al backend con CORS habilitado. Te lo marco ahora para que no construyas el backend y luego te encuentres con que la versión "bonita" en claude.ai no puede usarlo — esa versión publicada seguirá funcionando como demo con datos locales, pero la versión conectada al backend vivirá en otro sitio.

## 3. Dos rutas posibles — te recomiendo la B, pero empieza por A si quieres algo funcionando hoy mismo

**Ruta A — persistencia por documento (rápida, fiel al 100% a la arquitectura actual).**
Una sola tabla en Postgres:

```sql
create table patient_db (
  id          text primary key,       -- siempre 'vitalis-clinical-db-v3'
  data        jsonb not null,         -- el STATE completo tal cual lo serializa el frontend hoy
  updated_at  timestamptz not null default now()
);
```

Dos endpoints (`GET /api/state`, `PUT /api/state`) y un `ApiAdapter` en el frontend que implementa `load`/`save`/`remove` contra ellos en vez de `localStorage`. Prácticamente cero reescritura de servicios o de la interfaz — es literalmente el "sustituir `StorageAdapter` por un adaptador de API" que ya dejamos preparado. Tiene la limitante de que los datos no son consultables campo por campo desde SQL (no puedes hacer "todos los pacientes con prediabetes" en una query), pero te da persistencia real, multi-dispositivo, en minutos.

**Ruta B — modelo relacional completo (lo que pediste originalmente: datos consultables, editables, con historial real por entidad).**
Requiere migrar cada servicio del frontend de "mutar en memoria y llamar a `persist()`" a "llamar a un endpoint async por entidad". Es más trabajo, pero es la arquitectura correcta para una app clínica de verdad (reportes, multi-usuario, integridad referencial). El esquema y los endpoints están en las secciones 4 y 5.

Mi sugerencia concreta: pide a Claude Code que implemente la Ruta A primero (una tarde de trabajo, backend ya funcionando y desplegable), y migre entidad por entidad hacia la Ruta B cuando quieras invertir en eso — el propio `ApiAdapter` puede coexistir con endpoints específicos por entidad que se van añadiendo de a uno.

## 4. Esquema de datos (Ruta B)

Basado en el modelo que ya existe en el frontend (`DEFAULT_PATIENTS`, servicios en `index.html`):

```sql
create table patients (
  id uuid primary key default gen_random_uuid(),
  nombre text, apellidos text, fecha_nacimiento date, sexo text,
  documento text, telefono text, email text, direccion text,
  contacto_emergencia text,
  created_at timestamptz default now(), updated_at timestamptz default now()
);

create table antecedentes (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  categoria text not null,            -- personales|familiares|quirurgicos|alergias|reproductiva|nutricional
  status text not null,               -- no_evaluado|por_documentar|ausente|presente|desconocido|no_aplica
  descripcion text, fecha date, observaciones text,
  created_at timestamptz default now(), updated_at timestamptz default now()
);

create table symptoms (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  categoria text not null, nombre text not null,
  status text not null default 'no_evaluado',
  updated_at timestamptz default now()
);

create table nutrition_profile (       -- una fila por paciente
  patient_id uuid primary key references patients(id) on delete cascade,
  patron jsonb default '{}',           -- {comidas,horarios,regularidad,fuera,preparacion}
  calidad jsonb default '{}',          -- {fv,proteinas,cereales,grasas,fibra,ultraprocesados,azucares,bebidas}
  conducta jsonb default '{}',         -- {hambre,saciedad,velocidad,atencion,ansiedad,aburrimiento,antojos,nocturna}
  updated_at timestamptz default now()
);

create table food_diary_entries (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  fecha date, hora time, comida text, alimentos text,
  hambre int, saciedad int, contexto text,
  created_at timestamptz default now()
);

create table habits_profile (          -- una fila por paciente
  patient_id uuid primary key references patients(id) on delete cascade,
  actividad jsonb default '{}', sueno jsonb default '{}', estres jsonb default '{}',
  hidratacion jsonb default '{}', sustancias jsonb default '{}',
  updated_at timestamptz default now()
);

create table habit_tags (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  list_type text not null,             -- objetivos|barreras|facilitadores|resumen_objetivos
  texto text not null
);

create table habit_seguimiento (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  semana text, actividad int, alimentacion int, notas text,
  created_at timestamptz default now()
);

create table anthropometric_measurements (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  fecha date not null, peso numeric, talla numeric,
  imc numeric,                         -- calculado en el backend al insertar, no confiar en el cliente
  abdominal numeric, cintura numeric, cadera numeric,
  graso text, muscular text, observaciones text,
  created_at timestamptz default now()
);

create table vital_signs (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  fecha date not null, fc text, ta text, temp text, spo2 text, observaciones text,
  created_at timestamptz default now()
);

create table labs (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  nombre text not null, valor text, unidad text, rango text,
  fecha date, tendencia text, observaciones text,
  created_at timestamptz default now(), updated_at timestamptz default now()
);

create table medications (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  kind text not null,                  -- 'med' | 'sup'
  nombre text not null, dosis text, frecuencia text, via text,
  ingrediente text, fuente text,       -- solo aplican a suplementos
  inicio date, fin date, estado text default 'activa',  -- activa|inactiva
  motivo text, prescriptor text, observaciones text,
  created_at timestamptz default now(), updated_at timestamptz default now()
);

create table consultations (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  fecha date, hora time, profesional text,
  motivo text, expectativas text, objetivos text, prioridades text,
  inicio text, frecuencia text, desencadenantes text, alivian text,
  notas text, evaluacion text, plan text,
  estado text not null default 'borrador',   -- borrador|finalizada
  created_at timestamptz default now(), updated_at timestamptz default now()
);

create table resumen (                 -- una fila por paciente
  patient_id uuid primary key references patients(id) on delete cascade,
  situacion text,
  updated_at timestamptz default now()
);

create table resumen_problemas (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  nombre text not null, estado text, tone text
);

create table resumen_pendientes (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  texto text not null, fecha date
);

create table timeline_events (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid references patients(id) on delete cascade,
  ts timestamptz not null default now(),
  type text not null, title text not null, desc text
);
```

Nota de diseño: `timeline_events` se escribe explícitamente desde cada endpoint que muta datos (igual que hoy `TimelineService.log()` se llama desde cada servicio) — es más simple y más rápido de consultar que derivarlo con un `UNION` de las diez tablas en cada carga del dashboard.

## 5. Endpoints REST (Ruta B)

CRUD estándar por recurso, todos bajo `/api`:

- `GET/POST /patients`, `GET/PATCH /patients/{id}` (datos personales)
- `GET/POST/PATCH/DELETE /patients/{id}/antecedentes[/{aid}]`
- `GET /patients/{id}/symptoms`, `PATCH /patients/{id}/symptoms/{sid}` (cambia status)
- `GET/PATCH /patients/{id}/nutricion/{seccion}` (patron|calidad|conducta)
- `GET/POST/DELETE /patients/{id}/nutricion/diario[/{did}]`
- `GET/PATCH /patients/{id}/habitos/{dominio}` (actividad|sueno|estres|hidratacion|sustancias)
- `GET/POST/DELETE /patients/{id}/habitos/tags/{lista}[/{tid}]`
- `GET/POST /patients/{id}/habitos/seguimiento`
- `GET/POST/DELETE /patients/{id}/antropometria[/{mid}]` — el backend calcula el IMC, nunca confía en el valor del cliente
- `GET/POST/DELETE /patients/{id}/vitales[/{vid}]`
- `GET/POST/PATCH/DELETE /patients/{id}/labs[/{lid}]`
- `GET/POST/PATCH /patients/{id}/medicamentos[/{mid}]`, `.../suplementos[/{sid}]`, más `POST .../{mid}/toggle`
- `GET/POST/PATCH /patients/{id}/consultas[/{cid}]`, `POST .../{cid}/finalizar`
- `GET/PATCH /patients/{id}/resumen`
- `GET /patients/{id}/timeline`
- `GET /dashboard` — agregados calculados en el servidor (antes vivía en `computeDashboard()` del cliente)

## 6. Conectar el frontend

Sustituye `LocalStorageAdapter` por un `ApiAdapter`, y haz `loadState()`/`persist()` async (hoy son síncronos). Para la Ruta A el cambio es mínimo:

```js
var ApiAdapter = {
  load: async function(){ const r = await fetch('/api/state'); return r.ok ? (await r.json()).data : null; },
  save: async function(_key, value){ const r = await fetch('/api/state', {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({data:value})}); return r.ok; },
  remove: async function(){ await fetch('/api/state', {method:'DELETE'}); }
};
```

Para la Ruta B, cada método de servicio (`PatientService.create`, `LabService.add`, etc.) pasa de mutar `STATE` en memoria a hacer un `fetch` al endpoint correspondiente y luego actualizar `STATE` con la respuesta del servidor — así el servidor queda como fuente de verdad (por ejemplo, del IMC calculado).

## 7. Autenticación (pendiente, decisión tuya)

La app actual no tiene login: asume una sola clínica ("Dra. Ana Villegas") sin usuarios. Antes de manejar datos clínicos reales necesitas al menos una tabla `clinicians` y sesiones/JWT, y decidir si un paciente puede ver su propio historial o si esto es solo para el personal clínico. No lo incluí en el esquema de arriba a propósito — es una decisión de producto, no algo que deba asumir por ti.

## 8. Prompt listo para pegar en Claude Code

```
Estoy construyendo el backend para Vitalis, una app de historia clínica de medicina
funcional cuyo frontend ya existe (adjunto vitalis-frontend.html). Quiero un backend
en Python/FastAPI + PostgreSQL que reemplace el localStorage actual.

Empecemos por la Ruta A (persistencia rápida por documento): una tabla patient_db
con una columna jsonb, y dos endpoints GET/PUT /api/state que lean y escriban el
STATE completo tal como lo serializa hoy el frontend (revisa la función
Repo.persistAll() / Repo.loadAll() en vitalis-frontend.html para ver el formato
exacto). Usa SQLAlchemy + Alembic para las migraciones, Pydantic para validación,
y deja CORS configurado para desarrollo local. Sirve vitalis-frontend.html como
estático desde el propio FastAPI para evitar problemas de CORS/CSP.

Una vez funcionando, ayúdame a migrar hacia un modelo relacional completo
(pacientes, antecedentes, nutrición, hábitos, antropometría, laboratorios,
medicación, consultas, resumen, timeline) endpoint por endpoint, sin romper el
frontend en ningún punto intermedio.
```

## 9. Despliegue (cuando esté listo)

Opciones razonables para un backend FastAPI + Postgres pequeño: Render o Railway (Postgres gestionado incluido, despliegue directo desde tu repo de git) o Fly.io. Cualquiera de las tres te sirve para un demo con tráfico bajo sin gestionar servidores tú mismo.
