# OpenSpec en woptimizer

Este directorio implementa el patrón **OpenSpec** (https://openspec.dev/, Fission-AI) adaptado a este proyecto Python/Windows. NO usamos el CLI de OpenSpec (npm) — adoptamos la **estructura de carpetas y el flujo** para mantener dependencia cero con Node.js.

## Estructura

```
openspec/
├── specs/                    # Source of truth: requisitos canónicos
│   └── <capability>/
│       └── spec.md           # Formato SHALL — requisitos verificables
└── changes/                  # Propuestas de cambio (activas y cerradas)
    ├── <change-id>/          # Activa
    │   ├── proposal.md       # Why + What Changes + Impact
    │   └── tasks.md          # Pasos numerados de implementación
    └── archive/              # Cerradas (NO borrar — historial inmutable)
        └── <change-id>/
            ├── proposal.md
            └── tasks.md
```

## Flujo obligatorio

Ver `../AGENTS.md` sección "📜 Spec-Driven Development (SDD) — flujo OBLIGATORIO" para el detalle completo. Resumen:

1. Leer `AGENTS.md` + `llms.txt` (carga selectiva).
2. Crear `changes/<id>/proposal.md` con Why + What Changes + Impact.
3. Crear `changes/<id>/tasks.md` con pasos numerados.
4. Actualizar `AGENTS.md` (Spec-First) — spec rev +1.
5. Actualizar `openspec/specs/<cap>/spec.md` SOLO si la propuesta cambia una capacidad (via delta en `changes/<id>/specs/<cap>/spec.md`).
6. Implementar siguiendo `tasks.md`, tracking con `todowrite`.
7. Validar (correr tests del área).
8. Commit con mensaje `<id>: <descripción>`.
9. Mover `changes/<id>/` → `changes/archive/<id>/`.

## Cómo se relacionan los archivos

- `specs/<cap>/spec.md` describe QUÉ debe hacer el sistema.
- `changes/<id>/proposal.md` dice POR QUÉ vamos a cambiar algo y QUÉ areas toca.
- `changes/<id>/tasks.md` dice CÓMO vamos a implementarlo (pasos verificables).
- `changes/<id>/specs/<cap>/spec.md` (opcional) son **delta specs** — ADDED/MODIFIED/REMOVED sobre `specs/<cap>/spec.md`. Se mergean al cerrar la propuesta.
- `changes/archive/<id>/` es histórico inmutable.

## Capacidad inicial

- `specs/woptimizer/spec.md` — capacidad raíz del producto (todo woptimizer).

Las capacidades se irán creando según crezca el proyecto (ej: `specs/gaming/`, `specs/kill/`, `specs/profiles/`).

## Por qué OpenSpec pattern y no CLI

| Aspecto | OpenSpec CLI (npm) | Patrón carpeta (este proyecto) |
|---|---|---|
| Plataforma | Multi, requiere Node.js | Multi, sin dependencias |
| Validación de proposals | CLI valida schema | Manual (humano/IA lee) |
| Comandos | `openspec propose`, `openspec list`, etc. | Nativo (carpeta + git) |
| Adecuado para | Proyectos grandes con muchos contribuidores | Proyectos personales/pequeños |
| Coste setup | Medio (instalar + aprender CLI) | Bajo (crear carpetas) |

Woptimizer encaja en este último perfil: dueño único, IA-asistente, decisiones rápidas. Si crece y se多人 colaboran, podemos migrar al CLI.