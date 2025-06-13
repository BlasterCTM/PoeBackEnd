import sys
import os

# Asegura que la carpeta raíz esté en sys.path para que 'app' sea importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
