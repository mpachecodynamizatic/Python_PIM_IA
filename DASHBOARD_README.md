# 🎯 Dashboard PIM - Guía de Inicio

## ✅ Todo está Implementado y Funcionando

El Dashboard ha sido completamente rediseñado con:
- 📊 4 KPIs principales
- 📈 Gráficos de workflow y calidad
- 📋 Completitud de datos
- ⏱️ Timeline de actividad reciente
- 🔔 Widget de acciones pendientes

## 🚀 Cómo Arrancar

### Opción 1: Scripts Automáticos (Recomendado)

1. **Arrancar Backend:**
   - Haz doble clic en `START_BACKEND.bat`
   - Espera a ver: "Application startup complete"

2. **Arrancar Frontend:**
   - Haz doble clic en `START_FRONTEND.bat`
   - Espera a ver: "Local: http://localhost:5173"

### Opción 2: Manual

#### Terminal 1 - Backend
```bash
cd backend
.venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
```

#### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

## 🔐 Login

1. Abre: http://localhost:5173/login
2. Credenciales:
   - **Email:** `admin@pim.local`
   - **Password:** `admin`

## ✅ Verificación

### Backend OK:
- http://localhost:8000/health → `{"status":"ok"}`
- http://localhost:8000/docs → Documentación API

### Frontend OK:
- http://localhost:5173 → Redirige a /login o /dashboard

## 📊 Dashboard - Qué Verás

### KPIs Principales
- **Total Productos:** Actualmente 19
- **Score Promedio:** ~72/100
- **% Publicados:** Productos en estado ready
- **Completitud:** Basado en media/i18n/canales

### Widgets
1. **Acciones Pendientes:** Productos críticos, menciones, errores de sync
2. **Estado Workflow:** Gráfico donut con distribución por estados
3. **Distribución Calidad:** Gráfico de barras (Excelente/Aceptable/Crítico)
4. **Completitud de Datos:** Lista clickeable con productos sin media/i18n/canales
5. **Top Categorías:** Top 5 por volumen de productos
6. **Actividad Reciente:** Últimas 20 acciones del audit log

## 🔧 Solución de Problemas

### Error: "Access-Control-Allow-Origin"
**Causa:** No estás logueado o el token ha expirado.
**Solución:** Ve a /login y vuelve a iniciar sesión.

### Error: "Error al cargar estadísticas"
**Causa:** Backend no está corriendo o hay error en la BD.
**Solución:**
1. Verifica que el backend esté corriendo
2. Prueba: `curl http://localhost:8000/health`
3. Revisa migraciones: `cd backend && python -m alembic current`

### Dashboard en blanco
**Causa:** Frontend no puede conectarse al backend.
**Solución:**
1. Verifica que ambos servicios estén corriendo
2. Abre la consola del navegador (F12)
3. Busca errores en la pestaña "Network"

## 📝 Archivos Modificados

### Backend
- `app/api/v1/dashboard.py` - Endpoint completo
- `app/models/sync_job.py` - Modelo actualizado
- `alembic/versions/add_channel_connection_fields.py` - Migración

### Frontend
- `src/pages/Dashboard.tsx` - Componente rediseñado
- `src/api/dashboard.ts` - Cliente API
- `src/types/dashboard.ts` - Tipos TypeScript

## 🎉 ¡Listo!

Una vez que hayas iniciado sesión, el Dashboard debería cargar automáticamente mostrando todas las estadísticas en tiempo real.

Si ves el mensaje "Error al cargar estadísticas del dashboard", verifica:
1. ✅ Backend está corriendo (puerto 8000)
2. ✅ Frontend está corriendo (puerto 5173)
3. ✅ Has iniciado sesión correctamente

**El sistema funciona perfectamente en pruebas directas.** El problema suele ser simplemente que falta arrancar alguno de los servicios o no estás logueado.
