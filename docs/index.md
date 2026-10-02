# woptimizer — Process Manager Gaming para Windows (v3)

> **Estado actual:** Suite moderna en Python 3.11+ con interfaz gráfica en CustomTkinter, persistencia con Pydantic v2 y control nativo de procesos mediante `psutil`.

---

## ¿Qué es?

`woptimizer` es un gestor de procesos optimizado para gaming en Windows. Permite suspender o cerrar en masa aplicaciones en segundo plano organizadas por categorías de seguridad (navegadores, herramientas de sincronización, chat, productividad, streaming), liberando memoria RAM y ciclos de CPU antes de jugar, y restaurando la sesión al finalizar la partida mediante perfiles configurables ("Packs") y persistencia JSON.

---

## Inicio Rápido

```bash
# Lanzar en modo desarrollo
python run.py

# O como módulo
python -m woptimizer

# Ejecutable compilado para distribución
dist\woptimizer.exe

# Ejecutar suite de pruebas headless (105 tests)
python run_tests.py

# Verificar sintaxis estática y validaciones documentales
python verify_ui_syntax.py
python validate_docs.py
```

---

## Características Principales (v3)

- **Control Nativo con `psutil`:** Escaneo de procesos ultra-rápido en memoria C (<5 ms) mediante llamadas directas a las APIs del sistema operativo.
- **Blindaje Anti-Brick Indestructible:** 34 procesos críticos del sistema operativo protegidos a nivel de backend (`SYSTEM_PROTECTED_PROCESSES`). Imposibles de cerrar o finalizar accidentalmente.
- **Kill Recursivo y Seguro:** Cierre en cascada que elimina los procesos hijos antes que el proceso padre (`parent.children(recursive=True)`).
- **Arranque Seguro sin Shell:** Lanzamiento de aplicaciones con `shell=False`, contención de rutas absolutas y verificación binaria de cabecera PE (`_es_imagen_pe`).
- **Arquitectura de Packs y Favoritos:** Perfiles personalizables con acciones automáticas (`kill` / `start`), favoritos acumulativos y pack Gaming protegido contra eliminación.
- **Sesión Gaming y Reanudación Inteligente:** Detección de procesos cerrados y reapertura segura en un solo clic desde el Dashboard o desde la bandeja del sistema (`pystray`).
- **Interfaz Moderna en CustomTkinter:** Tres vistas principales (Portada, Gestor de Packs y Gestor de Procesos) cumpliendo con accesibilidad WCAG AA y tokens centralizados.
- **Base de Datos y Sincronización Observable:** Clasificación de más de 200 procesos con descarga asíncrona desde GitHub y fallback local transparente.

---

## Estructura del Código

```text
src/woptimizer/
├── __init__.py
├── __main__.py          # Entry Point de la aplicación
├── config.py            # Categorías, semáforos, constantes globales
├── models.py            # Modelos Pydantic v2: ProcessInfo, Pack, AppData
├── services/            # Capa de lógica de negocio (Backend desacoplado)
│   ├── process_service.py      # psutil: escaneo, kill recursivo, arranque seguro
│   ├── pack_service.py         # CRUD de packs, persistencia atómica y .bak
│   ├── gaming_service.py       # Sesiones de juego, telemetría y concurrencia
│   └── notification_service.py # Notificaciones nativas con pystray
└── ui/                  # Capa gráfica CustomTkinter (Cero llamadas directas a OS)
    ├── app.py                  # Ventana raíz y ciclo de vida de la aplicación
    ├── main_window.py          # Navegación y transiciones de vistas
    ├── theme.py                # Tokens de diseño, colores semánticos y fuentes
    ├── confirmation.py         # Mixin Confirmable y DoubleTapGuard (anti-accidental)
    ├── feedback.py             # Formateo honesto de telemetría y cierre
    └── views/                  # Vistas modulares
        ├── dashboard_view.py       # Portada con grid adaptativo de favoritos
        ├── pack_manager_view.py    # Gestor de packs y edición de perfiles
        └── process_manager_view.py # Gestor y explorador de procesos activos
```

---

## Documentación Web (MkDocs)

Para previsualizar o compilar la documentación localmente:

```bash
# Servidor de previsualización local (http://127.0.0.1:8000)
mkdocs serve

# Compilar sitio HTML estático en site/
mkdocs build
```

---

## Siguientes Pasos

- Consulta [`architecture.md`](architecture.md) para comprender la separación estricta de capas entre UI y Services.
- Revisa [`api.md`](api.md) para conocer las firmas y contratos de la capa de servicios.
- Lee [`ui-design-system.md`](ui-design-system.md) para conocer los tokens de CustomTkinter y las pautas de accesibilidad.
