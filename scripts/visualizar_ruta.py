"""Visualizador de la ruta optimizada para una tarea.

Uso rápido (PowerShell):

  # Instalar dependencias (si aún no)
  python -m pip install -r requirements.txt

  # Ejecutar con token explícito

python scripts/visualizar_ruta.py --id 35 --token "TU_TOKEN"
  
  THIS THIS IS THIS THE THING XDDD

  # O usando variable de entorno
  $env:POE_TOKEN="TU_TOKEN"; python scripts/visualizar_ruta.py --id 35

Argumentos:
  --id / -i        ID de la tarea (int)
  --token / -t     Bearer token (opcional si $POE_TOKEN está seteado)
  --base-url / -u  Base URL del backend (default http://localhost:8000)
  --no-invert-y    No invertir eje Y (por defecto se invierte para ver (0,0) arriba)

El endpoint consultado es: /api/v1/tareas/{id}/ruta-visual
"""
from __future__ import annotations
import os
import argparse
import sys
import requests
import matplotlib.pyplot as plt 
from typing import List, Dict

DEFAULT_BASE_URL = "http://localhost:8000"


def obtener_datos_ruta(id_tarea: int, token: str, base_url: str) -> Dict:
    url = f"{base_url.rstrip('/')}/{id_tarea}/ruta-visual"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def configurar_axes(ax, puntos: List[Dict], camino: List[Dict], invert_y: bool):
    # Determinar límites dinámicos según datos (más margen)
    xs = [p['x'] for p in camino] + [p.get('x_acceso', 0) for p in puntos]
    ys = [p['y'] for p in camino] + [p.get('y_acceso', 0) for p in puntos]
    if not xs or not ys:
        xs = [0]
        ys = [0]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    margen = 2
    ax.set_xlim(min_x - margen, max_x + margen)
    ax.set_ylim(min_y - margen, max_y + margen)

    # Ticks enteros
    ax.set_xticks(range(min_x - margen, max_x + margen + 1))
    ax.set_yticks(range(min_y - margen, max_y + margen + 1))
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    if invert_y:
        ax.invert_yaxis()
        ax.xaxis.tick_top()


def dibujar_ruta(ax, camino: List[Dict]):
    ruta_x = [p['x'] for p in camino]
    ruta_y = [p['y'] for p in camino]
    ax.plot(ruta_x, ruta_y, color='#3498db', linewidth=2, zorder=1, label='Caminata')

    # Flechas cada 2 segmentos
    for i in range(0, len(ruta_x) - 1, 2):
        dx = ruta_x[i + 1] - ruta_x[i]
        dy = ruta_y[i + 1] - ruta_y[i]
        if dx != 0 or dy != 0:
            ax.arrow(ruta_x[i], ruta_y[i], dx * 0.5, dy * 0.5,
                     head_width=0.3, head_length=0.3,
                     fc='#2980b9', ec='#2980b9', zorder=2)

    if ruta_x and ruta_y:
        ax.scatter(ruta_x[0], ruta_y[0], color='green', s=150, label='Inicio', zorder=3, edgecolors='black')


def dibujar_paradas(ax, paradas: List[Dict]):
    for parada in paradas:
        px = parada.get('x_acceso')
        py = parada.get('y_acceso')
        if px is None or py is None:
            continue
        nombre_producto = parada.get('nombre_producto', 'Producto')
        orden = parada.get('orden', '?')
        etiqueta = f"{orden}. {nombre_producto}"
        ax.scatter(px, py, color='#e74c3c', s=100, zorder=3, edgecolors='black')
        ax.annotate(etiqueta, (px, py),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.8),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))


def visualizar(id_tarea: int, token: str, base_url: str, invert_y: bool):
    print(f"📡 Consultando ruta para Tarea {id_tarea}...")
    try:
        data = obtener_datos_ruta(id_tarea, token, base_url)
    except Exception as e:
        print(f"❌ Error al conectar con API: {e}")
        return 1

    camino = data.get('coordenadas_ruta', [])
    paradas = data.get('puntos_visita', [])

    fig, ax = plt.subplots(figsize=(10, 10))
    configurar_axes(ax, paradas, camino, invert_y=invert_y)
    dibujar_ruta(ax, camino)
    dibujar_paradas(ax, paradas)

    tiempo = data.get('tiempo_estimado_min')
    plt.title(f"Visualización Ruta Tarea {id_tarea} (Tiempo: {tiempo} min)", y=1.05)
    plt.legend(loc='lower right')
    print("✅ Mostrando ventana de visualización...")
    plt.show()
    return 0


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description="Visualizador de ruta de picking para una tarea.")
    parser.add_argument('--id', '-i', type=int, required=True, help='ID de la tarea a consultar')
    parser.add_argument('--token', '-t', type=str, help='Bearer token (si no se usa $POE_TOKEN)')
    parser.add_argument('--base-url', '-u', type=str, default=DEFAULT_BASE_URL, help='Base URL del backend')
    parser.add_argument('--no-invert-y', action='store_true', help='No invertir eje Y (por defecto se invierte)')
    return parser.parse_args(argv)


def main(argv: list[str]):
    args = parse_args(argv)
    token = args.token or os.getenv('POE_TOKEN')
    if not token:
        print("❌ Debes proporcionar un token con --token o variable de entorno POE_TOKEN")
        return 2
    return visualizar(args.id, token, args.base_url, invert_y=not args.no_invert_y)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
