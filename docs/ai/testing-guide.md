# Guía de Pruebas y Validación para Agentes IA

## Desafío en Entornos Headless
En muchos entornos de IA no existe un monitor o display activo de Windows conectado directamente al proceso del agente. Si un script ejecuta `app.mainloop()` de CustomTkinter, el script se quedará bloqueado de forma indefinida esperando interacción humana.

## Patrones de Prueba Obligatorios

### 1. Validación Estática de Sintaxis e Imports (`py_compile`)
Antes de dar por terminada cualquier edición de UI o servicios, compilar los archivos a bytecode:
```python
import py_compile
py_compile.compile('src/woptimizer/ui/app.py', doraise=True)
py_compile.compile('src/woptimizer/models.py', doraise=True)
```

### 2. Prueba de Inicialización Headless de la UI
Para verificar que los widgets cargan y los componentes se instancian sin errores de runtime:
```python
app = WOptimizerApp(process_service, pack_service, gaming_service)
# Programar cierre automático tras 1000ms para no bloquear la consola
app.root.after(1000, app.root.destroy)
app.run()
```

### 3. Pruebas Unitarias de Backend
Probar `process_service` y `pack_service` con tests independientes en `tests/` o scripts temporales sin levantar Tkinter.
