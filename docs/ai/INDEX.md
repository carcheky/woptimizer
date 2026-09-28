# 📚 Sistema de Documentación Modular para IAs (Índice Maestro)

Este directorio implementa el estándar de **Carga Selectiva de Contexto (Progressive Disclosure)** para agentes IA.
En lugar de cargar toda la documentación en el prompt y saturar la ventana de contexto, el agente debe leer este índice o el archivo raíz `llms.txt` y cargar **únicamente el módulo relevante para su tarea actual**.

---

## 🗂️ Módulos de Documentación Disponibles

| Módulo | Ruta | Cuándo cargarlo | Tamaño aprox. |
|---|---|---|:---:|
| **Arquitectura y Capas** | [`architecture.md`](docs/ai/architecture.md) | Al modificar la separación de capas, agregar nuevos servicios o entender el flujo de datos. | ~60 líneas |
| **Modelos de Datos y JSON** | [`data-models.md`](docs/ai/data-models.md) | Al trabajar con `models.py`, `profiles.json`, persistencia o esquemas de Packs. | ~80 líneas |
| **Diseño y UI CustomTkinter** | [`ui-design-system.md`](docs/ai/ui-design-system.md) | Al crear o editar vistas, botones, temas, diálogos o navegación de ventanas. | ~100 líneas |
| **Reglas de Sandbox y Windows** | [`sandbox-rules.md`](docs/ai/sandbox-rules.md) | Al ejecutar comandos de terminal, solucionar errores de permisos (EPERM) o compilar con PyInstaller. | ~70 líneas |
| **Guía de Pruebas y Validación** | [`testing-guide.md`](docs/ai/testing-guide.md) | Al ejecutar tests, verificar sintaxis estática o validar la UI sin pantalla física. | ~50 líneas |

---

## 🤖 Protocolo Obligatorio para Agentes IA
1. **Paso 1:** Al iniciar una tarea, consulta `.taskmaster/tasks.json` (o ejecuta `python .taskmaster/tm.py next`) para conocer el módulo asociado a tu tarea.
2. **Paso 2:** Lee **únicamente** ese archivo con `view_file`.
3. **Paso 3:** No leas los demás archivos a menos que sea estrictamente necesario por dependencias cruzadas.
