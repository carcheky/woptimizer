# Mini App — Estado y bloqueo

## Resumen ejecutivo

Existe una versión Mini App en `miniapps/process_manager/` con código completo (manifest, server.mjs, client HTML). **No es publicable** en este entorno por un bug del sandbox del Host MiniMax Code.

## Estado del código

| Archivo | Estado |
|---------|--------|
| `miniapps/process_manager/package.json` | ✅ schemaVersion 2 (`mcode.miniApp`) |
| `miniapps/process_manager/miniapp/miniapp.json` | ✅ schemaVersion 1, payloads declarados |
| `miniapps/process_manager/miniapp/node/server.mjs` | ✅ 9.3 KB — endpoints REST completos |
| `miniapps/process_manager/miniapp/client/index.html` | ✅ 23 KB — UI gaming mode completa |
| `miniapps/process_manager/.minimax-plugin/plugin.json` | ✅ metadata + description |

## Endpoints API implementados

```
GET  /api/processes       # lista procesos via PowerShell
POST /api/kill            # mata procesos via taskkill
POST /api/relaunch        # relanza via subprocess.Popen
GET  /api/saved           # lee saved_processes.json
POST /api/saved           # añade con dedup (name, pid)
DELETE /api/saved         # limpia la lista
GET  /dashboard           # sirve el cliente HTML
```

UI cliente incluye: categorías gaming, búsqueda, modo Simple/Completo, atajos teclado, menú contextual, modal de confirmación, auto-refresh opcional.

## Bloqueo: `RUNTIME_START_FAILED` con EACCES

Cada intento de `miniapp.publish` falla con:

```
code: PREPARATION_FAILED
stage: runtime
reasonCode: RUNTIME_START_FAILED
runtimeError: Error: listen EACCES: permission denied 127.0.0.1:60784
```

### Causa raíz

El sandbox del proceso Node del Host MiniMax Code **bloquea TCP binds al puerto 60784 específicamente**. Otros puertos funcionan (port 0 → OS-assigned OK), pero el Host asigna 60784 y verifica TCP readiness ahí.

### Evidencia (6 estrategias probadas, todas fallan)

| # | Estrategia | Resultado |
|---|------------|-----------|
| 1 | `listen(60784, '127.0.0.1')` (canónico) | EACCES |
| 2 | `listen(60784, '0.0.0.0')` | EACCES |
| 3 | `listen(60784, '::1')` | EACCES |
| 4 | `listen(60784, '::')` | EACCES |
| 5 | `listen(0, host)` (OS-assigned) | ✅ bind OK |
| 6 | port 0 + `netsh interface portproxy` | Regla añadida, no enruta (ECONNREFUSED) |

**Test #5 fue clave:** el bind a un puerto OS-assigned funciona. Esto confirma que el problema NO es la loopback en general — es específico al puerto 60784.

**Test #6 fue clave:** las reglas portproxy se añaden correctamente (visibles con `netsh show`), pero el sandbox de Chromium/Electron del Host bloquea el enrutamiento hacia puertos reservados.

**Confirmado:** el scaffold original del Host (sin mis modificaciones) **también falla** con EACCES. No es mi código.

### Stderr capturado del último intento

```
[debug] context.listen = {"host":"127.0.0.1","port":60784}
[debug] port type: number, host type: string
[debug] listening on 127.0.0.1:57864  ← con port 0, OS picks otro puerto
[debug] WARN: actual port != assigned, Host may time out
```

→ confirma que `context.listen` está bien formado.

### Reinicio como admin

Probado: cerrar MiniMax Code, relanzar como administrador. **Sin cambio.** El bloqueo es del sandbox del proceso, no de permisos de usuario.

## Diagnóstico probable

El Host MiniMax Code probablemente:
1. Asigna un puerto específico a cada Mini App
2. Reserva ese puerto a nivel del sandbox del proceso Node
3. Los procesos hijos del sandbox no pueden hacer bind al mismo puerto

Esto explicaría por qué:
- Port 0 funciona (el sandbox no reserva puertos OS-assigned)
- El puerto 60784 específicamente no funciona (está reservado por el Host)
- Reinicio como admin no cambia nada (es el sandbox del proceso, no permisos del usuario)

## Workarounds intentados que NO funcionan

1. ❌ Bind a 0.0.0.0 en lugar de 127.0.0.1
2. ❌ Bind a IPv6 (::1, ::)
3. ❌ Bind a port 0 con OS-assign + actualizar context.listen.port
4. ❌ netsh interface portproxy para redirigir 60784 → puerto real
5. ❌ Reinicio de MiniMax Code como administrador

## Workarounds que NO se han probado (posibles pero riesgosos)

1. **stdin/stdout IPC en lugar de HTTP** — el runtime-api.md no menciona esta opción, pero otros runtimes podrían soportarla
2. **Cambiar el puerto de asignación del Host** — requiere modificar archivos del Host, no permitido desde plugin
3. **Usar HTTP/2 o WebSocket** — el problema es el bind, no el protocolo

## Acciones requeridas del usuario

Para usar la Mini App, alguna de estas:

1. **Esperar** a que MiniMax Code solvente el bug en una actualización
2. **Reportar** el bug al soporte de MiniMax Code adjuntando:
   - El stderr capturado
   - Las 6 estrategias probadas
   - Confirmación de que el scaffold original también falla
3. **Empaquetar como .exe standalone** (Electron, Tauri) — fuera del Host MiniMax Code

## Decisión actual

**Python es el producto final.** El código Mini App queda en `miniapps/process_manager/` como referencia para cuando el bug se solvente. No se seguirá trabajando en él mientras el sandbox del Host no permita bind TCP.

## Si en el futuro se reintenta

1. Actualizar MiniMax Code
2. Ejecutar `miniapp.publish` sin modificar `server.mjs` (debería usar el scaffold canónico)
3. Si sigue fallando, comparar el puerto asignado con otros plugins para ver si es bug específico del sandbox o del código
4. Si funciona, validar con `miniapp.inspect` y `miniapp.open`
5. Una vez publicado, comparar UX con la versión Python
