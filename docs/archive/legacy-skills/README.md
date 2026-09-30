# Skills heredadas (ciclo 21)

Estas tres skills se movieron aquí el **2026-09-30** y **no están en uso**. No
las borres: están conservadas como historial y para poder comparar qué cambió
al pasar de skill a subagente.

| Carpeta | Skill original | Reemplazada por |
|---|---|---|
| `architect/` | `architect-review` como skill | `.agents/agents/architect-review/agent.md` |
| `openspec-dev/` | `openspec-dev` como skill | `.agents/agents/openspec-dev/agent.md` |
| `process-db-updater/` | `process-db-updater` como skill | `.agents/agents/process-db-updater/agent.md` |

`.agents/skills/id-pipeline/` **no** se movió: esa sigue viva, es la que
orquesta el bucle.

## Por qué se movieron

Porque una skill y un subagente son **mecanismos distintos** y una skill no
puede hacer lo que el pipeline necesitaba:

| | Skill | Subagente |
|---|---|---|
| Dónde vive | `.agents/skills/<n>/SKILL.md` | `.agents/agents/<n>/agent.md` |
| Quién la ejecuta | el orquestador, en su propia sesión | una sesión propia, delegada con `task` |
| Contexto | comparte el del orquestador | **no lo hereda**: hay que pasarle contexto |
| ¿Se ve en el panel de agentes? | no | sí |

El ciclo 16 movió los roles de skill a subagente por eso, y este archivo
recuerda por qué. Se quedaron aquí porque en su día nadie las borró, y el
resultado era un nombre (`openspec-dev`) que significaba dos cosas distintas
según dónde mirases.

## La trampa que tendía

Un tercer motor, o cualquier agente leyendo el repo, se encontraba con
`openspec-dev` **en dos sitios** y **sin ninguna nota de cuál mandar**, porque
los dos ficheros se llamaban igual. La regla general que dejó este caso:

> **Un artefacto de instrucciones que pierde frente a otro del mismo nombre no
> se archiva a medias. O se borra, o se marca como muerto en el sitio donde
> estaba.**

En este repo la opción de borrar está descartada por norma del propietario, así
que toca archivar. Y como estas skills son texto plano, siguen siendo
legibles por cualquier IA aunque no estén activas.
