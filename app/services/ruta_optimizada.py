from sqlalchemy.orm import Session, joinedload
from typing import List, Tuple, Dict, Any
from app.models.tarea import Tarea
from app.models.detalle_tarea import DetalleTarea
from app.models.punto_reposicion import PuntoReposicion
from app.models.mueble_reposicion import MuebleReposicion
from app.models.ubicacion_fisica import UbicacionFisica
from app.models.objeto_mapa import ObjetoMapa
from app.models.mapa import Mapa
from app.models.objeto_tipo import ObjetoTipo
from app.repositories.ruta import generar_grafo
from app.utils.astar import astar
from app.schemas.ruta_detallada import RutaOptimizadaCreate, DetalleRutaCreate, PasoRutaCreate
from app.repositories.ruta_detallada import RutaDetalladaRepository
import math
from datetime import date

class RutaService:
    def __init__(self, db: Session):
        self.db = db

    def optimizar_tarea(self, id_tarea: int, id_empresa: int, algoritmo: str = "vecino_mas_cercano"):
        """
        Orquestador principal: Recibe ID tarea -> Devuelve Ruta Optimizada Guardada.
        """
        # 1. Carga Eficiente de Datos (Solución al N+1)
        tarea, detalles = self._cargar_datos_tarea(id_tarea, id_empresa)
        if not detalles:
            raise ValueError("La tarea no tiene detalles para optimizar.")

        mapa = self._obtener_mapa_activo(id_empresa)
        if not mapa:
            raise ValueError("No hay un mapa activo para esta empresa.")

        # 2. Generar Grafo de Navegación (Set de coordenadas caminables)
        walkable_nodes = generar_grafo(self.db, mapa.id_mapa)

        # 2.1 Obtener punto de inicio dinámico (Entrada) o fallback (0,0)
        punto_inicio = self._obtener_punto_inicio(mapa.id_mapa)
        # Aseguramos que el punto de inicio esté considerado caminable
        walkable_nodes.add(punto_inicio)
        print(f"[INFO] Punto de inicio de la ruta: {punto_inicio}")

        # 3. Identificar Puntos de Interés y sus Accesos
        nodos_objetivo = self._procesar_puntos_visita(detalles, mapa.id_mapa, walkable_nodes)

        # 4. Ejecutar Algoritmo TSP (Ordering) desde el punto de inicio real
        orden_visita = self._resolver_tsp(nodos_objetivo, algoritmo, start_pos=punto_inicio)
        ruta_completa_data = self._generar_camino_fisico(orden_visita, walkable_nodes, start_pos=punto_inicio)

        # [NUEVO] LIMPIEZA PREVENTIVA: Borrar rutas antiguas de esta tarea
        self._limpiar_rutas_anteriores(id_tarea)

        # 6. Persistencia Transaccional
        ruta_guardada = self._guardar_ruta(tarea, ruta_completa_data)
        
        return ruta_guardada

    def _cargar_datos_tarea(self, id_tarea: int, id_empresa: int):
        """Obtiene toda la info necesaria en 1 o 2 consultas optimizadas."""
        tarea = self.db.query(Tarea).filter(Tarea.id_tarea == id_tarea, Tarea.id_empresa == id_empresa).first()
        if not tarea:
            raise ValueError("Tarea no encontrada.")

        detalles = (
            self.db.query(DetalleTarea)
            .join(PuntoReposicion, DetalleTarea.id_punto == PuntoReposicion.id_punto)
            .join(MuebleReposicion, PuntoReposicion.id_mueble == MuebleReposicion.id_mueble)
            .join(ObjetoMapa, MuebleReposicion.id_objeto == ObjetoMapa.id_objeto)
            .filter(DetalleTarea.id_tarea == id_tarea)
            .options(
                joinedload(DetalleTarea.punto)
                .joinedload(PuntoReposicion.mueble)
                .joinedload(MuebleReposicion.objeto)
            )
            .all()
        )
        return tarea, detalles

    def _obtener_mapa_activo(self, id_empresa: int):
        """Devuelve el único mapa ACTIVO de la empresa.
        - Si no hay ninguno: None
        - Si hay más de uno: lanza ValueError (inconsistencia de datos)
        """
        mapas_activos = (
            self.db.query(Mapa)
            .filter(Mapa.id_empresa == id_empresa, Mapa.activo == True)
            .all()
        )
        if not mapas_activos:
            return None
        if len(mapas_activos) > 1:
            raise ValueError("Hay múltiples mapas activos para la empresa. Debe existir solo uno.")
        return mapas_activos[0]

    def _obtener_punto_inicio(self, id_mapa: int) -> Tuple[int, int]:
        """Busca coordenadas (x,y) de un objeto tipo 'Entrada'. Fallback (0,0)."""
        tipo_entrada = self.db.query(ObjetoTipo).filter(ObjetoTipo.nombre_tipo.ilike("salida")).first()
        if tipo_entrada:
            ubicacion_entrada = (
                self.db.query(UbicacionFisica)
                .join(ObjetoMapa, UbicacionFisica.id_objeto == ObjetoMapa.id_objeto)
                .filter(
                    UbicacionFisica.id_mapa == id_mapa,
                    ObjetoMapa.id_tipo == tipo_entrada.id_tipo
                )
                .first()
            )
            if ubicacion_entrada:
                return (ubicacion_entrada.x, ubicacion_entrada.y)
        return (0, 0)

    def _procesar_puntos_visita(self, detalles: List[DetalleTarea], id_mapa: int, walkable: set) -> List[Dict]:
        """
        Para cada producto, encuentra dónde está el mueble y cuál es el punto caminable más cercano.
        """
        nodos_procesados = []

        for det in detalles:
            mueble = det.punto.mueble
            objeto_mapa = mueble.objeto
            
            coords_mueble = (
                self.db.query(UbicacionFisica)
                .filter(UbicacionFisica.id_objeto == objeto_mapa.id_objeto, UbicacionFisica.id_mapa == id_mapa)
                .all()
            )
            
            if not coords_mueble:
                print(f"[WARN] El mueble {objeto_mapa.nombre} no tiene ubicación física en el mapa.")
                continue

            # Pasamos el punto específico (con estantería/nivel) para orientar el acceso
            access_point = self._encontrar_mejor_acceso(coords_mueble, walkable, mueble, det.punto)
            
            if not access_point:
                print(f"[WARN] Inaccesible: Mueble {objeto_mapa.nombre} en {coords_mueble[0].x},{coords_mueble[0].y} está bloqueado.")
                continue

            nodos_procesados.append({
                "detalle": det,
                "target_coords": access_point,
                "mueble_coords": (coords_mueble[0].x, coords_mueble[0].y),
                "mueble_id": mueble.id_mueble
            })
        
        return nodos_procesados

    def _encontrar_mejor_acceso(self,
        coords_mueble: List[UbicacionFisica],
        walkable: set,
        mueble: MuebleReposicion,
        punto_especifico: PuntoReposicion
    ) -> Tuple[int, int]:
        """
        1) Filtra accesos por Dirección (N/S/E/O).
        2) Prioriza el acceso más cercano a la columna/estantería del producto.
        Asume coordenadas pantalla (0,0 arriba-izquierda), y aumenta hacia abajo.
        """
        if not coords_mueble:
            return None

        xs = [c.x for c in coords_mueble]
        ys = [c.y for c in coords_mueble]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        ancho_fisico = (max_x - min_x) + 1
        alto_fisico = (max_y - min_y) + 1
        es_horizontal = ancho_fisico > alto_fisico

        total_cols = max(1, mueble.columnas)
        col_actual = max(0, min((punto_especifico.estanteria or 1) - 1, total_cols - 1))
        ratio = col_actual / total_cols if total_cols > 1 else 0.5

        if es_horizontal:
            target_x = min_x + (ancho_fisico * ratio)
            target_y = min_y + (alto_fisico / 2)
        else:
            target_x = min_x + (ancho_fisico / 2)
            target_y = min_y + (alto_fisico * ratio)
        target_slot = (target_x, target_y)

        deltas_map = {
            'N': [(0, -1)], 'S': [(0, 1)], 'E': [(1, 0)], 'O': [(-1, 0)],
            'T': [(0, 1), (0, -1), (1, 0), (-1, 0)]
        }
        dir_mueble = mueble.direccion if getattr(mueble, 'direccion', None) else 'T'
        deltas = deltas_map.get(dir_mueble, deltas_map['T'])

        candidatos = []
        for celda in coords_mueble:
            for dx, dy in deltas:
                vecino = (celda.x + dx, celda.y + dy)
                if vecino in walkable:
                    candidatos.append(vecino)
        if not candidatos:
            return None

        mejor_candidato = None
        menor_distancia = float('inf')
        for cand in candidatos:
            dist = math.sqrt((cand[0] - target_slot[0])**2 + (cand[1] - target_slot[1])**2)
            if dist < menor_distancia:
                menor_distancia = dist
                mejor_candidato = cand
        return mejor_candidato

    def _resolver_tsp(self, nodos: List[Dict], algoritmo: str, start_pos: Tuple[int, int]) -> List[Dict]:
        """
        Ordena la lista de nodos usando Vecino Más Cercano Global.
        """
        if not nodos:
            return []
        pendientes = nodos.copy()
        ordenados = []
        pos_actual = start_pos
        while pendientes:
            mejor_nodo = None
            dist_minima = float('inf')
            idx_mejor = -1
            for i, nodo in enumerate(pendientes):
                target = nodo["target_coords"]
                dist = abs(target[0] - pos_actual[0]) + abs(target[1] - pos_actual[1])
                if dist < dist_minima:
                    dist_minima = dist
                    mejor_nodo = nodo
                    idx_mejor = i
            ordenados.append(mejor_nodo)
            pos_actual = mejor_nodo["target_coords"]
            pendientes.pop(idx_mejor)
        return ordenados

    def _generar_camino_fisico(self, nodos_ordenados: List[Dict], walkable: set, start_pos: Tuple[int, int]):
        """
        Calcula el A* real entre cada punto ordenado.
        """
        if not nodos_ordenados:
            return None
        pos_actual = start_pos
        tiempo_total = 0.0
        distancia_total = 0.0
        detalles_ruta_out = []
        pasos_por_detalle_out = []
        secuencia_paso_global = 1
        for nodo in nodos_ordenados:
            destino = nodo["target_coords"]
            camino = astar(pos_actual, destino, walkable)
            if not camino and pos_actual != destino:
                print(f"[ERROR] No hay camino de {pos_actual} a {destino}")
                camino = [pos_actual, destino]
            dist_segmento = len(camino) if camino else 0
            tiempo_segmento = dist_segmento * 2.5
            distancia_total += dist_segmento
            tiempo_total += tiempo_segmento
            tiempo_total += 30
            pasos_db = []
            for coord in camino:
                pasos_db.append(PasoRutaCreate(
                    id_detalle_ruta=0,  # ID dummy, real se asigna al persistir
                    secuencia=secuencia_paso_global,
                    x=coord[0],
                    y=coord[1]
                ))
                secuencia_paso_global += 1
            # Guardar lista de pasos separada por detalle
            pasos_por_detalle_out.append(pasos_db)
            detalles_ruta_out.append(DetalleRutaCreate(
                id_ruta=0,  # ID dummy, real se asigna al persistir
                orden=len(detalles_ruta_out) + 1,
                id_punto=nodo["detalle"].id_punto,
                tiempo_estimado_punto=tiempo_segmento + 30,
                id_detalle_tarea=nodo["detalle"].id_detalle
            ))
            pos_actual = destino
        return {
            "tiempo_estimado": tiempo_total,
            "distancia_total": distancia_total,
            "detalles": detalles_ruta_out,
            "pasos_por_detalle": pasos_por_detalle_out
        }

    def _guardar_ruta(self, tarea: Tarea, ruta_data: dict):
        if not ruta_data:
            return None
        ruta_in = RutaOptimizadaCreate(
            id_reponedor=tarea.id_reponedor,
            id_tarea=tarea.id_tarea,
            id_empresa=tarea.id_empresa,
            fecha_generada=date.today(),
            algoritmo_usado="vecino_mas_cercano_global",
            tiempo_estimado=ruta_data["tiempo_estimado"],
            distancia_total=ruta_data["distancia_total"]
        )
        return RutaDetalladaRepository.crear_ruta_completa(
            self.db,
            ruta_in,
            ruta_data["detalles"],
            ruta_data["pasos_por_detalle"]
        )

    def _limpiar_rutas_anteriores(self, id_tarea: int):
        """Elimina rutas obsoletas para evitar duplicados en la BD."""
        from app.models.ruta_optimizada import RutaOptimizada
        rutas_viejas = (
            self.db.query(RutaOptimizada)
            .filter(RutaOptimizada.id_tarea == id_tarea)
            .all()
        )
        for ruta in rutas_viejas:
            self.db.delete(ruta)
        # Dejar que el commit del repositorio de ruta detallada persista los cambios
        self.db.flush()
