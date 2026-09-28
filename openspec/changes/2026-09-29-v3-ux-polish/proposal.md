# Change Proposal: v3-ux-polish

## Contexto y Por Qué
Tras la implementación fundacional de la V3, la UI básica funciona pero carece de usabilidad avanzada y flexibilidad. El usuario necesita interactuar de forma transparente con la base de datos de procesos, comprender visualmente el riesgo de cerrar aplicaciones, y tener poder de personalización sobre el motor central de optimización (el Pack Gaming).

Además, el uso de CSV, aunque ligero, no es óptimo jerárquicamente frente a JSON (soportado nativamente por Pydantic) y los endpoints remotos apuntaban a repositorios genéricos en lugar del destino final real del usuario en GitLab.

## Alcance del Cambio

### 1. Evolución de la Base de Datos (CSV a JSON)
- **Motivación:** JSON es igual de ligero en disco y memoria, pero ofrece tipado estricto, anidación y se integra nativamente con los modelos Pydantic existentes en el proyecto.
- **Cambio:** Migrar `assets/fallback.csv` a `assets/process_db.json`.
- **Endpoint Remoto:** Actualizar los servicios para que el botón de descarga apunte a `https://gitlab.com/carcheky/woptimizer/-/raw/main/assets/process_db.json`.

### 2. UI: Transparencia y Riesgo de Procesos
- **Gestor de Procesos:** La lista de procesos en vivo debe mostrar el semáforo de seguridad (🟢/🟡/🔴) junto a cada ejecutable reconocido, junto con su descripción.
- **Actualización Manual:** Proveer un botón explícito en la UI para "🔄 Actualizar Base de Datos de Procesos", dando control al usuario sin depender únicamente de la descarga asíncrona oculta.

### 3. Personalización del Pack Gaming
- El Pack "Gaming" es intocable estructuralmente, pero sus *reglas* deben ser editables.
- **Edición en UI:** Permitir desde el Gestor de Packs añadir o quitar ejecutables específicos al Pack Gaming, y ofrecer un menú/checkboxes para decidir qué categorías (ej. `Sincronización`, `Navegadores`) debe afectar el proceso de optimización.

## Criterios de Aceptación
- Un usuario lego puede entender visualmente por qué un proceso no debe cerrarse gracias a las descripciones y el semáforo en pantalla.
- Se puede modificar la agresividad del modo Gaming (activando/desactivando categorías) desde la interfaz gráfica.
- El sistema obtiene sus datos desde la URL oficial de GitLab usando formato JSON parseado directamente a Pydantic.
