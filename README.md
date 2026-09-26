# woptimizer

Process Manager con foco gamer para Windows.

## Quick start

Doble clic en `dist\woptimizer.exe` (recomendado) — auto-eleva como admin, sin instalar nada.
Alternativa legacy: doble clic en `ProcessManager.vbs` (requiere Python 3.13 + tkinter instalado).

## Documentación

| Recurso | Para qué |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Spec única para agentes IA. Léeme siempre al empezar/cerrar. |
| [`llms.txt`](llms.txt) | Índice curado para cargar selectivamente con un agente IA. |
| [`llms-full.txt`](llms-full.txt) | Texto completo concatenado (40 KB). |
| [`docs/index.md`](docs/index.md) | Portal de la documentación detallada. |
| [`openspec/README.md`](openspec/README.md) | Cómo funciona el flujo SDD (Spec-Driven Development) aquí. |
| [`openspec/specs/`](openspec/specs/) | Requisitos canónicos en formato `SHALL`. |
| [`openspec/changes/`](openspec/changes/) | Propuestas de cambio activas. |
| [`openspec/changes/archive/`](openspec/changes/archive/) | Cambios cerrados (historial). |

### Servir docs localmente

```bash
pip install mkdocs mkdocs-material pymdown-extensions
mkdocs serve
```

Abrir http://localhost:8000 en el navegador.

Para generar el sitio estático:

```bash
mkdocs build --strict
```

## Estado

- ✅ v2.1.0 funcional — UI gaming completa, perfiles, ejecutable standalone
- ✅ Flujo SDD + llms.txt para carga selectiva de docs por agentes
- ❌ Mini App no publicable (bloqueo del sandbox del Host MiniMax Code, ver `docs/mini-app-status.md`)
