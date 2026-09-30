# Agentes del pipeline

Los cuatro roles del motor `/id-pipeline`, en el formato que Antigravity
reconoce: Markdown con frontmatter YAML de `name` + `description`.

| Agente | Papel en el bucle | Responde a |
|---|---|---|
| `architect-review` | Paso 2, planear. Audita premisas antes de tocar código. | ¿Es esto viable y seguro? |
| `openspec-dev` | Paso 3, ejecutar. Escribe código, tests y docs. | ¿Funciona y está probado? |
| `mutation-auditor` | Paso 4, auditar. Rompe el código a propósito. | ¿El test se enteraría si el código estuviera mal? |
| `process-db-updater` | Área 3, datos. Escanea procesos y alimenta `process_db.json`. | ¿Qué procesos hay y cuáles son seguros de cerrar? |

## Dónde vive cada copia, y por qué hay dos

```
.agents/agents/<n>/agent.md   <-- FUENTE DE VERDAD. Versionada, viaja con el repo.
~/.minimax/agents/<n>/        <-- ESPEJO. Solo en esta maquina, no versionada.
```

Los dos runtimes que las usan **no comparten configuración**: MiniMax Code
busca agentes en `~/.minimax/agents/`, Antigravity en `.agents/agents/`. Por eso
la duplicación no es un descuido que se pueda borrar: es el precio de que el
mismo rol funcione en los dos.

Pero duplicado sin control es drift silencioso, y el drift aquí es caro: un
agente que se corrigió en el repo y no en el espejo sigue dando el consejo viejo
a la mitad del equipo. Para eso está el sincronizador:

```bash
python .taskmaster/sync_agents.py --check   # informa, no escribe. exit 1 si diverge
python .taskmaster/sync_agents.py           # espejo repo -> global
```

**Edita siempre la copia del repo.** Si editas el espejo global, el cambio se
pierde en el siguiente `sync`.

## Claves de frontmatter disponibles en Antigravity

Los ficheros usan solo `name` y `description`, que es lo obligatorio y lo que
comparten ambos runtimes. Antigravity además acepta, opcionalmente:

| Clave | Por defecto | Para qué sirve |
|---|---|---|
| `tools` | `[]` | Lista blanca de herramientas del subagente. |
| `model` | `inherit` | Palier de modelo al invocarlo. |
| `commandExecutionPolicy` | `sandbox` | Política de ejecución de shell. |
| `mcpServers` | `[]` | Servidores MCP del subagente. |
| `mainAgent` | `true` | Si puede seleccionarse como agente principal. |
| `subagent` | `true` | Si el agente principal puede delegar en él. |

**No se han añadido a proposito.** Este repo no tiene forma de probarlas, y un
frontmatter mal puesto puede impedir que el agente cargue sin dar ningún error
visible. Si añades alguna, pruébala en Antigravity antes de commitearla.

## Portabilidad

Los cuatro agentes están escritos **contra este repo**: citan
`.taskmaster/git_safe_commit.py`, el VFS de Nextcloud, `run_tests.py`, las
trampas documentadas en `docs/known-issues.md` y hablan de `woptimizer` en
`description`. En Antigravity sobre este repositorio funcionan tal cual.

En **otro** proyecto son activamente engañosos, porque empujan al agente a
buscar ficheros que no existen. Si los quieres reutilizar fuera, quítales la
capa de repo y deja el método: el núcleo de cada uno (auditar premisas antes de
implementar / mutar el código a proposito) no es específico de woptimizer.

## Trampa al ejecutar shell desde aquí

`mutation-auditor` y `openspec-dev` lanzan comandos. En Windows, la consola es
`cp1252` y **PowerShell parsea el bloque entero antes de ejecutar nada**:

- `print()` con acentos, flechas o emoji lanza `UnicodeEncodeError`. Escribe
  en ASCII puro.
- Una regex pasada a `python -c` rompe el parseo y **anula también las líneas
  correctas del mismo bloque**. Escribe un `.py` temporal y ejecútalo.

Ambas están en `docs/known-issues.md` (Trampas #16 y #18) y en el `agent.md` de
cada rol. Si un agente nuevo de este repo las ignora, va a perder tiempo
exactamente como lo perdieron ellos.
