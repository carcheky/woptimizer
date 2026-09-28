# 🎮 woptimizer v3

> Cierra las apps que sobran cuando vas a jugar.
> Reabre tu setup de trabajo cuando vuelves.

## ✨ Features

- 🚀 **Gaming mode**: Un click para cerrar navegadores, sincronización y procesos pesados.
- 📦 **Packs**: Configura qué aplicaciones reabrir después de jugar (tu perfil de usuario favorito).
- 🔒 **Keepers**: Discord se queda (o lo que configures).
- ⚡ **Rápido**: Escrito con `psutil`, lista y mata procesos instantáneamente.
- 🎨 **Moderno**: Interfaz totalmente renovada con `CustomTkinter`.
- 🛡️ **Admin**: Se auto-eleva para matar procesos protegidos sin problemas.

## 📥 Descarga / Instalación

### Opción 1: Ejecutable (Sin instalar Python)
1. Descarga el archivo `woptimizer.exe` desde la sección de **Releases** en GitHub.
2. Haz doble clic y acepta los permisos de administrador (UAC). ¡Listo!

### Opción 2: Ejecutar desde código fuente
Si tienes Python 3.11+ instalado y prefieres correrlo nativo:
```bash
# Clonar repo
git clone https://.../woptimizer.git
cd woptimizer

# Instalar dependencias
pip install -e ".[dev]"

# Arrancar la app
python -m woptimizer
```

## 🛠️ Stack Tecnológico (v3)
- Interfaz gráfica: **CustomTkinter**
- Motor de procesos: **psutil**
- Persistencia JSON: **Pydantic**
- CI/CD & Build: **PyInstaller + GitHub Actions**

---
*Hecho para gamers que odian el lag.*
