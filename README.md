# 🎮 woptimizer v3

> Cierra las apps que sobran cuando vas a jugar. Reabre tu setup cuando vuelves.
> Pensado para que no tengas que pensar en qué procesos te están robando FPS.

![Estado del proyecto](https://img.shields.io/badge/ciclos-20-blue) ![Tests](https://img.shields.io/badge/tests-57%20verdes-brightgreen)

**Changelog:** [`CHANGELOG.md`](CHANGELOG.md) · **Tablero:** [`STATUS.md`](STATUS.md) · **Docs técnicas:** [`docs/ai/`](docs/ai/INDEX.md)

---

## ✨ Qué hace

| Función | En la práctica |
|---|---|
| 🚀 **Gaming Mode** | Un botón que cierra navegadores, sincronización de ficheros y procesos pesados. Tienes que **pulsar dos veces** para que ocurra: la primera solo avisa. |
| 📦 **Packs** | Agrupa apps en perfiles. Cada pack sabe si debe **cerrarlas** o **abrirlas**. El pack Gaming viene protegido: no se puede borrar. |
| 🎯 **Por categorías** | En vez de listar app por app, marca la categoría entera ("🟢 Navegadores") y el motor decide. |
| 🔒 **Keepers** | Lo que proteges nunca se cierra, aunque su categoría esté marcada para cerrar. Discord y Steam vienen fuera por defecto. |
| 🟢🟡🔴 **Semáforo de seguridad** | Cada proceso lleva un color: 🟢 se puede cerrar, 🟡 con cuidado, 🔴 **nunca se toca**. |
| 📊 **Qué has ganado** | Después de cada acción, un banner dice cuántos procesos se cerraron y **cuánta RAM se liberó**. |
| 🔔 **Avisos en Windows** | Notificación del sistema al cerrar o abrir cosas, aunque la ventana esté minimizada. |
| 📥 **Bandeja del sistema** | Cerrar la ventana la minimiza a la bandeja. Desde ahí: mostrar la app, preparar Gaming Mode, o salir. |
| 💾 **No pierdes tu configuración** | Los packs se guardan con copia de seguridad automática y se recuperan solos si el archivo se corrompe. |

---

## 🛡️ Lo que **no** va a hacer

Esto es tan importante como lo que sí:

- **No mata procesos de sistema.** Hay 34 nombres (lsass, csrss, winlogon, dwm…) blindados por tres capas independientes, y una barrera extra que impide cerrar una categoría roja aunque la marques por error.
- **No borra tu configuración.** Si el archivo de packs se corrompe, se recupera de la copia de seguridad. Si falta permiso para escribir, te avisa en vez de sobrescribir.
- **No te mata el PC por un fallo propio.** Cada cierre pasa siempre por la misma puerta de seguridad, y los tests comprueban esa puerta rompiendo el código a propósito.

---

## 📥 Instalación

### Opción 1 — Ejecutable (no necesitas Python)
1. Descarga `woptimizer.exe` de la sección **Releases** de GitHub.
2. Doble clic. Windows te pedirá permisos de administrador: acéptalos y la app se abre.
   *(El `.exe` se compila con `--uac-admin`, por eso pide elevación. Al ejecutarla desde
   código con `python run.py` no la pide.)*

> El ejecutable se reconstruye periódicamente. La versión publicada puede ir por detrás del código fuente: mira la fecha del último cambio en el changelog.

### Opción 2 — Desde el código
Necesitas **Python 3.11+**.

```bash
git clone <url-del-repo>
cd woptimizer
pip install -e ".[dev]"
python run.py
```

Otros comandos:

```bash
python -m woptimizer      # equivalente a run.py
python run_tests.py       # 91 tests headless (no abre ventanas)
python verify_ui_syntax.py
```

---

## 🧭 Cómo se organiza

```text
src/woptimizer/
├── config.py       # Categorías, semáforos, procesos protegidos
├── models.py       # Modelos Pydantic: Pack, ProcessInfo, AppData
├── services/       # TODA la lógica. Único sitio que habla con el SO.
│   ├── process_service.py     # psutil: listar, matar, arrancar
│   ├── pack_service.py        # Packs + persistencia + backups
│   ├── gaming_service.py      # La política del Gaming Mode
│   └── notification_service.py
└── ui/             # Solo pintan. Nunca leen ficheros ni llaman a psutil.
```

**La regla que no se rompe:** la interfaz nunca toca el sistema operativo ni los JSON directamente. Pasa por `services/`. Es lo que permite que los tests corran sin abrir una ventana.

---

## 🛠️ Stack

`Python 3.11+` · `CustomTkinter` (UI) · `psutil` (procesos) · `pydantic v2` (modelos) · `PyInstaller` (build) · `pytest`-style suite propia en `run_tests.py`

---

## 📚 Documentación

| Documento | Para qué |
|---|---|
| [`CHANGELOG.md`](CHANGELOG.md) | Qué cambió, en humano. **Empieza por aquí.** |
| [`STATUS.md`](STATUS.md) | Salud del sistema y deuda técnica conocida. |
| [`docs/known-issues.md`](docs/known-issues.md) | Las trampas del proyecto y por qué existen. |
| [`AGENTS.md`](AGENTS.md) | Cómo trabaja un agente de IA en este repo. |
| [`docs/ai/`](docs/ai/INDEX.md) | Referencia técnica por capa. |

---

<div align="center">
<sub>Hecho para gamers que odian el lag.</sub>
</div>
