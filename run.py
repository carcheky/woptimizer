import sys
import os

# Añadimos la carpeta 'src' al path de Python para que pueda encontrar 'woptimizer'
sys.path.insert(0, os.path.abspath('src'))

from woptimizer.__main__ import main

if __name__ == '__main__':
    sys.exit(main())
