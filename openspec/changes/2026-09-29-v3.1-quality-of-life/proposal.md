# Propuesta: v3.1 Quality of Life (QoL) e Integración de Sistema

## Contexto y Motivación
Tras finalizar la versión 3 (rediseño UI, base de datos JSON asíncrona, orquestación de packs), la herramienta es 100% funcional y altamente intuitiva. Sin embargo, carece de integraciones profundas con el sistema operativo que harían su uso mucho más pasivo y seguro.

Esta especificación propone añadir características de "Quality of Life" sugeridas durante la auditoría arquitectónica del final de la v3.

## Objetivos (What)
1. **System Tray (Bandeja del Sistema):** Permitir que la ventana principal no se cierre, sino que se oculte en la bandeja del sistema (junto al reloj). Esto permitirá usar la app como un servicio residente.
2. **Menú Contextual en Tray:** Añadir clic derecho al icono de la bandeja para mostrar un menú rápido que permita "Apagar Apps del Pack Gaming" sin tener que abrir la UI grande.
3. **Auto-Backup de Perfiles:** Cada vez que el `pack_service` guarde `profiles.json`, se creará automáticamente un backup rotativo (ej. `profiles.bak`) para prevenir pérdida de configuraciones por apagones.
4. **Sistema de Logging Ligero:** Implementar un logger en un archivo local (`woptimizer.log`) para registrar las advertencias asíncronas y fallos de permisos EPERM.

## Arquitectura (How)
- **Tray:** Se utilizará la librería estándar y liviana `pystray` combinada con `PIL` para renderizar el icono de la bandeja. Se interceptará el evento `WM_DELETE_WINDOW` de CustomTkinter para ocultar la ventana en lugar de destruirla (`self.withdraw()`).
- **Backup:** En `PackService.save()`, antes de abrir en modo escritura (`w`), se usará `shutil.copy` para duplicar el archivo si existe.
- **Logging:** Se instanciará la librería estándar `logging` en `config.py` inyectando manejadores de rotación de archivos.
