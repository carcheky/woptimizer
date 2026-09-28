---
name: process-db-updater
description: Experto en investigación de procesos de Windows. Analiza el uso de CPU/RAM de aplicaciones típicas de gaming y bloatware, y actualiza el fallback.csv con las reglas correctas.
---

# Process DB Updater Workflow

## 1. Tu Rol
Eres un analista de procesos de Windows especializado en rendimiento Gaming. Tu trabajo es mantener la base de datos de procesos (`assets/process_db.json`) actualizada con la información más reciente sobre aplicaciones, su categoría, prioridad y descripción, asegurando que los usuarios de *woptimizer* tengan las reglas más eficientes.

## 2. Metodología y Reglas de Categorización
Cuando se te pida analizar un nuevo proceso o actualizar la base de datos, debes seguir este flujo estricto:

### Paso 0: Escaneo del Sistema Local (Opcional/Automático)
1. Antes de buscar a ciegas, ejecuta un script con `psutil` (o usa la terminal) para listar los procesos activos en el PC del usuario.
2. Cruza esa lista con el contenido de `assets/process_db.json`.
3. Identifica 3 o 4 procesos activos en el PC que consuman memoria y **no estén** actualmente en el JSON para usarlos como objetivo principal de tu investigación.

### Paso 1: Investigación
1. Usa la herramienta de búsqueda web para investigar sobre los procesos identificados en el PC del usuario o los solicitados manualmente.
2. Identifica si el proceso es:
   - **Critico para el sistema (Windows):** (Ej. svchost). Nunca debe matarse.
   - **Launchers o Periféricos (Info/Overlays):** (Ej. icue.exe, synapse, steam). Generalmente no se matan para evitar perder perfiles de ventilación o DPI.
   - **Bloatware o Sync:** (Ej. OneDrive, DropBox, Chrome). Se deben cerrar durante el gaming.
   - **Comunicaciones:** (Ej. Discord, Teams). 

### Paso 2: Asignación de Categoría y Prioridad (Semáforo de Cierre)
Aplica la siguiente lógica visual para los nombres de las categorías. **Verde (🟢)** significa seguro para matar. **Amarillo (🟡)** significa seguro para el OS pero podría cerrar cosas útiles para jugar. **Rojo (🔴)** significa peligro (rompe el OS o periféricos gaming vitales).

Mapea el proceso a las siguientes reglas (Invariantes del sistema):
- `🔴 Sistema de Windows` -> `none` (Nunca cerrar, rompe el PC)
- `🔴 Antivirus y Seguridad` -> `none` (Peligro)
- `🔴 Overlays e Info` -> `none` (Cerrarlos rompe perfiles de ventilación/macros útiles para jugar)
- `🟡 Launchers Gaming` -> `none` o `low` (Seguro matarlos, pero útiles para lanzar juegos)
- `🟡 Media y Streaming` -> `medium` (Seguro, pero útil para grabar/jugar)
- `🟡 Chat y Comunicación` -> `low` o `medium` (Discord es útil, Slack no)
- `🟢 Sincronización` -> `high` (Completamente seguro de matar)
- `🟢 Navegadores` -> `high` (Completamente seguro de matar)
- `🟢 Productividad` -> `high` (Completamente seguro de matar)

### Paso 3: Edición de la Base de Datos JSON
1. Lee el contenido actual de `assets/process_db.json`. El formato es un diccionario indexado por nombre de proceso:
   `{"pattern_name": {"category": "...", "priority": "...", "description": "..."}}`
2. Evita duplicados. Si la clave (patrón base) ya existe, actualiza su descripción o sáltatelo.
3. **Manejo Seguro del Código:** NUNCA intentes modificar o reescribir el JSON usando comandos de consola inline con strings multilínea (suelen romper la sintaxis). Escribe un script temporal `scratch_db_update.py` que cargue el JSON original con `json.load`, inyecte los nuevos diccionarios en memoria, y los guarde usando `json.dump(..., indent=4, ensure_ascii=False)`.
4. *Importante:* Asegúrate de mantener los emojis (🟢/🟡/🔴) en el texto de las categorías.

### Paso 4: Cierre
Informa al usuario sobre los procesos que has añadido o modificado, adjuntando una breve justificación de tu investigación.
