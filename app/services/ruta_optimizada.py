import random
import itertools
from fastapi import HTTPException
from app.schemas.ruta_detallada import RutaOptimizadaCreate, DetalleRutaCreate, PasoRutaCreate
from app.repositories.ruta_detallada import RutaDetalladaRepository
from datetime import date

# Importa los modelos y dependencias necesarias según tu estructura
# from app.models import ...
# from app.schemas import ...
# from app.core.security import ...

# Los algoritmos de optimización de rutas

def algoritmo_vecino_mas_cercano(puntos_info, inicio, coordenadas_caminables):
    """
    Algoritmo del vecino más cercano - el actual implementado
    """
    puntos_restantes = puntos_info.copy()
    posicion_actual = inicio
    orden_visita_coords = [inicio]
    orden_visita_puntos = []

    while puntos_restantes:
        punto_mas_cercano = None
        distancia_minima = float('inf')
        for punto in puntos_restantes:
            coordenadas_punto = punto['coordenadas']
            distancia = abs(posicion_actual[0] - coordenadas_punto[0]) + abs(posicion_actual[1] - coordenadas_punto[1])
            if distancia < distancia_minima:
                distancia_minima = distancia
                punto_mas_cercano = punto
        if punto_mas_cercano:
            orden_visita_coords.append(punto_mas_cercano['coordenadas'])
            orden_visita_puntos.append(punto_mas_cercano)
            posicion_actual = punto_mas_cercano['coordenadas']
            puntos_restantes.remove(punto_mas_cercano)
    
    return orden_visita_coords, orden_visita_puntos, "Vecino Más Cercano + A*", "Algoritmo de optimización que utiliza el vecino más cercano para ordenar los puntos y A* para calcular las rutas entre ellos"

def algoritmo_fuerza_bruta(puntos_info, inicio, coordenadas_caminables):
    """
    Algoritmo de fuerza bruta - prueba todas las permutaciones posibles
    """
    if len(puntos_info) > 8:  # Limitar para evitar explosión combinatoria
        puntos_muestra = random.sample(puntos_info, 8)
    else:
        puntos_muestra = puntos_info
    
    mejor_distancia = float('inf')
    mejor_orden = None
    
    for permutacion in itertools.permutations(puntos_muestra):
        distancia_total = 0
        pos_actual = inicio
        for punto in permutacion:
            coord_punto = punto['coordenadas']
            distancia_total += abs(pos_actual[0] - coord_punto[0]) + abs(pos_actual[1] - coord_punto[1])
            pos_actual = coord_punto
        if distancia_total < mejor_distancia:
            mejor_distancia = distancia_total
            mejor_orden = permutacion
    
    orden_visita_coords = [inicio]
    orden_visita_puntos = []
    for punto in mejor_orden:
        orden_visita_coords.append(punto['coordenadas'])
        orden_visita_puntos.append(punto)
    
    return orden_visita_coords, orden_visita_puntos, "Fuerza Bruta + A*", "Algoritmo que prueba todas las permutaciones posibles para encontrar la ruta óptima (limitado a 8 puntos máximo)"

def algoritmo_genetico(puntos_info, inicio, coordenadas_caminables):
    """
    Algoritmo genético simple para optimización de rutas
    """
    if len(puntos_info) < 2:
        return algoritmo_vecino_mas_cercano(puntos_info, inicio, coordenadas_caminables)
    
    POBLACION_SIZE = min(20, len(puntos_info) * 2)
    GENERACIONES = 50
    TASA_MUTACION = 0.1
    
    def calcular_fitness(orden):
        distancia_total = 0
        pos_actual = inicio
        for punto in orden:
            coord_punto = punto['coordenadas']
            distancia_total += abs(pos_actual[0] - coord_punto[0]) + abs(pos_actual[1] - coord_punto[1])
            pos_actual = coord_punto
        return 1.0 / (distancia_total + 1)
    
    def crear_individuo():
        return random.sample(puntos_info, len(puntos_info))
    
    def cruzar(padre1, padre2):
        tamano = len(padre1)
        inicio_idx = random.randint(0, tamano - 2)
        fin_idx = random.randint(inicio_idx + 1, tamano - 1)
        hijo = [None] * tamano
        hijo[inicio_idx:fin_idx + 1] = padre1[inicio_idx:fin_idx + 1]
        restantes = [item for item in padre2 if item not in hijo]
        idx_restante = 0
        for i in range(tamano):
            if hijo[i] is None:
                hijo[i] = restantes[idx_restante]
                idx_restante += 1
        return hijo
    
    def mutar(individuo):
        if random.random() < TASA_MUTACION:
            i, j = random.sample(range(len(individuo)), 2)
            individuo[i], individuo[j] = individuo[j], individuo[i]
        return individuo
    
    poblacion = [crear_individuo() for _ in range(POBLACION_SIZE)]
    for generacion in range(GENERACIONES):
        fitness_scores = [(individuo, calcular_fitness(individuo)) for individuo in poblacion]
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        nueva_poblacion = [individuo for individuo, _ in fitness_scores[:POBLACION_SIZE // 4]]
        while len(nueva_poblacion) < POBLACION_SIZE:
            padre1 = random.choices(fitness_scores[:POBLACION_SIZE // 2], weights=[f for _, f in fitness_scores[:POBLACION_SIZE // 2]])[0][0]
            padre2 = random.choices(fitness_scores[:POBLACION_SIZE // 2], weights=[f for _, f in fitness_scores[:POBLACION_SIZE // 2]])[0][0]
            hijo = cruzar(padre1, padre2)
            hijo = mutar(hijo)
            nueva_poblacion.append(hijo)
        poblacion = nueva_poblacion
    mejor_individuo = max(poblacion, key=calcular_fitness)
    orden_visita_coords = [inicio]
    orden_visita_puntos = []
    for punto in mejor_individuo:
        orden_visita_coords.append(punto['coordenadas'])
        orden_visita_puntos.append(punto)
    return orden_visita_coords, orden_visita_puntos, "Algoritmo Genético + A*", f"Algoritmo genético con {GENERACIONES} generaciones y población de {POBLACION_SIZE} individuos para optimizar la ruta"

# Servicio principal para obtener la ruta optimizada

def obtener_ruta_optimizada(
    id_tarea,
    algoritmo,
    db,
    current_user,
    Tarea,
    UsuarioModel,
    EstadoTarea,
    DetalleTarea,
    Mapa,
    UbicacionFisica,
    ObjetoMapa,
    ObjetoTipo,
    PuntoReposicion,
    MuebleReposicion,
    Producto,
    generar_grafo,
    encontrar_punto_accesible_cruz,
    encontrar_punto_accesible,
    calcular_ruta,
    CoordenadaResponse,
    MuebleRutaResponse,
    ProductoRutaResponse,
    PuntoRutaResponse,
    AlgoritmoResponse,
    RutaOptimizadaResponse,
    RolEnum
):
    """
    Servicio para obtener la ruta optimizada de una tarea específica.
    """
    algoritmos_disponibles = {
        "vecino_mas_cercano": algoritmo_vecino_mas_cercano,
        "fuerza_bruta": algoritmo_fuerza_bruta,
        "genetico": algoritmo_genetico
    }
    if algoritmo not in algoritmos_disponibles:
        raise HTTPException(
            status_code=400,
            detail=f"Algoritmo '{algoritmo}' no válido. Algoritmos disponibles: {list(algoritmos_disponibles.keys())}"
        )
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if current_user.rol.nombre_rol == RolEnum.SUPERVISOR.value and tarea.id_supervisor != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea")
    elif current_user.rol.nombre_rol == RolEnum.REPONEDOR.value and tarea.id_reponedor != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta tarea")
    reponedor = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == tarea.id_reponedor).first()
    if not reponedor:
        raise HTTPException(status_code=400, detail="La tarea no tiene reponedor asignado")
    estado = db.query(EstadoTarea).filter(EstadoTarea.estado_id == tarea.estado_id).first()
    estado_nombre = estado.nombre_estado if estado else "Desconocido"
    detalles = db.query(DetalleTarea).filter(DetalleTarea.id_tarea == id_tarea).all()
    if not detalles:
        raise HTTPException(status_code=400, detail="La tarea no tiene productos asignados")
    
    # Buscar mapa activo primero, fallback al primer mapa disponible
    mapa = db.query(Mapa).filter(Mapa.activo == True).first()
    if not mapa:
        print("[WARNING] No hay mapa activo definido, usando el primer mapa disponible")
        mapa = db.query(Mapa).first()
    if not mapa:
        raise HTTPException(status_code=500, detail="No hay mapas configurados en el sistema")
    print(f"[DEBUG] [obtener_ruta_optimizada] Llamando a generar_grafo para mapa {mapa.id_mapa}")
    coordenadas_caminables = generar_grafo(db, mapa.id_mapa)
    print(f"[DEBUG] [obtener_ruta_optimizada] Total coordenadas caminables: {len(coordenadas_caminables)}")
    ubicaciones_muebles = db.query(UbicacionFisica).join(ObjetoMapa).join(ObjetoTipo).filter(ObjetoTipo.nombre_tipo == "mueble").all()
    muebles_coords = set((ubic.x, ubic.y) for ubic in ubicaciones_muebles)
    coordenadas_caminables -= muebles_coords
    puntos_info = []
    coordenadas_puntos = []
    for detalle in detalles:
        punto = db.query(PuntoReposicion).filter(PuntoReposicion.id_punto == detalle.id_punto).first()
        if not punto:
            continue
        mueble = db.query(MuebleReposicion).filter(MuebleReposicion.id_mueble == punto.id_mueble).first()
        if not mueble:
            continue
        objeto = db.query(ObjetoMapa).filter(ObjetoMapa.id_objeto == mueble.id_objeto).first()
        if not objeto:
            continue
        ubicaciones = db.query(UbicacionFisica).filter(UbicacionFisica.id_objeto == objeto.id_objeto).all()
        if not ubicaciones:
            continue
        producto = db.query(Producto).filter(Producto.id_producto == detalle.id_producto).first()
        if not producto:
            continue
        print(f"[DEBUG] [obtener_ruta_optimizada] Detalle {detalle.id_detalle}: punto={punto.id_punto}, mueble={mueble.id_mueble}, ubicaciones={[ (u.x, u.y) for u in ubicaciones ]}")
        coordenada_accesible = None
        for ubic in ubicaciones:
            print(f"[DEBUG] [obtener_ruta_optimizada] Buscando punto accesible para mueble en ({ubic.x}, {ubic.y})")
            c = encontrar_punto_accesible_cruz((ubic.x, ubic.y), coordenadas_caminables)
            print(f"[DEBUG] [obtener_ruta_optimizada] Punto accesible encontrado: {c}")
            if c != (0, 0):
                coordenada_accesible = c
                break
        if not coordenada_accesible:
            print(f"[WARNING] [obtener_ruta_optimizada] No se encontró punto accesible para detalle {detalle.id_detalle}, usando (0,0)")
            coordenada_accesible = (0, 0)
        coordenadas_puntos.append(coordenada_accesible)
        coordenada_display = CoordenadaResponse(x=ubicaciones[0].x, y=ubicaciones[0].y)
        mueble_info = MuebleRutaResponse(
            id_mueble=mueble.id_mueble,
            nombre_objeto=objeto.nombre,
            coordenadas=coordenada_display,
            nivel=punto.nivel,
            estanteria=punto.estanteria
        )
        producto_info = ProductoRutaResponse(
            id_producto=producto.id_producto,
            nombre=producto.nombre,
            categoria=producto.categoria,
            cantidad=detalle.cantidad
        )
        puntos_info.append({
            'id_punto': punto.id_punto,
            'mueble': mueble_info,
            'producto': producto_info,
            'coordenadas': coordenada_accesible,
            'coordenadas_originales': [(ubic.x, ubic.y) for ubic in ubicaciones]
        })
    if not puntos_info:
        raise HTTPException(
            status_code=400, 
            detail="No se pudieron obtener las coordenadas para los puntos de reposición"
        )
    inicio = (0, 0)
    distancia_total = 0
    if inicio not in coordenadas_caminables:
        inicio = encontrar_punto_accesible(inicio, coordenadas_caminables)
    algoritmo_func = algoritmos_disponibles[algoritmo]
    print(f"[DEBUG] [obtener_ruta_optimizada] Origen inicial: {inicio}")
    print(f"[DEBUG] [obtener_ruta_optimizada] Puntos a visitar (coordenadas): {[p['coordenadas'] for p in puntos_info]}")
    orden_visita_coords, orden_visita_puntos, nombre_algoritmo, descripcion_algoritmo = algoritmo_func(
        puntos_info, inicio, coordenadas_caminables
    )
    print(f"[DEBUG] [obtener_ruta_optimizada] Orden de visita calculado: {orden_visita_coords}")
    coordenadas_ruta_completa = []
    ruta_valida = True
    for i in range(len(orden_visita_coords) - 1):
        origen = orden_visita_coords[i]
        destino = orden_visita_coords[i + 1]
        print(f"[DEBUG] [obtener_ruta_optimizada] Calculando ruta de {origen} a {destino}")
        ruta_segmento = calcular_ruta(
            db,
            mapa.id_mapa,
            origen,
            destino
        )
        print(f"[DEBUG] [obtener_ruta_optimizada] Ruta calculada: {ruta_segmento}")
        if ruta_segmento:
            ruta_segmento_filtrada = []
            for idx, coord in enumerate(ruta_segmento):
                if coord in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                    ruta_valida = False
                    break
                ruta_segmento_filtrada.append(coord)
            if not ruta_valida:
                print(f"[ERROR] [obtener_ruta_optimizada] Ruta inválida: pasa por mueble en {coord}")
                break
            if i == 0:
                coordenadas_ruta_completa.extend(ruta_segmento_filtrada)
            else:
                coordenadas_ruta_completa.extend(ruta_segmento_filtrada[1:])
            distancia_total += len(ruta_segmento_filtrada) - 1
        else:
            print(f"[WARNING] [obtener_ruta_optimizada] No se pudo calcular ruta entre {origen} y {destino}")
            if i == 0:
                coordenadas_ruta_completa.append(origen)
            x1, y1 = origen
            x2, y2 = destino
            ruta_manual = []
            if x1 < x2:
                for x in range(x1 + 1, x2 + 1):
                    if (x, y1) in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                        ruta_valida = False
                        break
                    ruta_manual.append((x, y1))
            elif x1 > x2:
                for x in range(x1 - 1, x2 - 1, -1):
                    if (x, y1) in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                        ruta_valida = False
                        break
                    ruta_manual.append((x, y1))
            if not ruta_valida:
                print(f"[ERROR] [obtener_ruta_optimizada] Ruta manual inválida: pasa por mueble")
                break
            x_final = x2
            if y1 < y2:
                for y in range(y1 + 1, y2 + 1):
                    if (x_final, y) in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                        ruta_valida = False
                        break
                    ruta_manual.append((x_final, y))
            elif y1 > y2:
                for y in range(y1 - 1, y2 - 1, -1):
                    if (x_final, y) in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
                        ruta_valida = False
                        break
                    ruta_manual.append((x_final, y))
            if not ruta_valida:
                print(f"[ERROR] [obtener_ruta_optimizada] Ruta manual inválida: pasa por mueble")
                break
            coordenadas_ruta_completa.extend(ruta_manual)
            distancia_total += len(ruta_manual)
    print(f"[DEBUG] [obtener_ruta_optimizada] Ruta global final: {coordenadas_ruta_completa}")
    if coordenadas_ruta_completa:
        while coordenadas_ruta_completa and coordenadas_ruta_completa[-1] in [(ubic.x, ubic.y) for ubic in ubicaciones_muebles]:
            coordenadas_ruta_completa.pop()
        if not coordenadas_ruta_completa:
            ruta_valida = False
    if not ruta_valida:
        raise HTTPException(
            status_code=400,
            detail="No se pudo generar una ruta válida que no pase ni termine sobre un mueble. Verifique la disposición del mapa y los puntos de reposición."
        )
    if coordenadas_ruta_completa:
        ultima_coord = coordenadas_ruta_completa[-1]
        if ultima_coord in muebles_coords:
            adyacentes_cruz = [
                (ultima_coord[0], ultima_coord[1] + 1),
                (ultima_coord[0], ultima_coord[1] - 1),
                (ultima_coord[0] + 1, ultima_coord[1]),
                (ultima_coord[0] - 1, ultima_coord[1])
            ]
            nueva_ultima = None
            for coord in reversed(coordenadas_ruta_completa):
                if coord in muebles_coords:
                    continue
                if coord in adyacentes_cruz:
                    nueva_ultima = coord
                    break
            if nueva_ultima:
                idx_nueva = coordenadas_ruta_completa.index(nueva_ultima)
                coordenadas_ruta_completa = coordenadas_ruta_completa[:idx_nueva + 1]
            else:
                for coord in reversed(coordenadas_ruta_completa):
                    if coord not in muebles_coords:
                        nueva_ultima = coord
                        break
                if nueva_ultima:
                    idx_nueva = coordenadas_ruta_completa.index(nueva_ultima)
                    coordenadas_ruta_completa = coordenadas_ruta_completa[:idx_nueva + 1]
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="No se pudo ajustar la ruta final para evitar terminar sobre un mueble."
                    )
    puntos_ordenados = []
    for idx, punto in enumerate(orden_visita_puntos, start=1):
        punto_respuesta = PuntoRutaResponse(
            id_punto=punto['id_punto'],
            mueble=punto['mueble'],
            producto=punto['producto'],
            orden_visita=idx
        )
        puntos_ordenados.append(punto_respuesta)
    coordenadas_respuesta = [CoordenadaResponse(x=x, y=y) for x, y in coordenadas_ruta_completa]
    algoritmo_info = AlgoritmoResponse(
        nombre=nombre_algoritmo,
        descripcion=descripcion_algoritmo
    )
    tiempo_estimado = distancia_total + (len(puntos_ordenados) * 2)
    rutas_previas = RutaDetalladaRepository.obtener_rutas_por_tarea(db, tarea.id_tarea)
    for r in rutas_previas:
        if r.id_reponedor == reponedor.id_usuario:
            RutaDetalladaRepository.eliminar_ruta(db, r.id_ruta)
    ruta_data = RutaOptimizadaCreate(
        id_reponedor=reponedor.id_usuario,
        id_tarea=tarea.id_tarea,
        fecha_generada=date.today(),
        algoritmo_usado=nombre_algoritmo,
        tiempo_estimado=tiempo_estimado,
        distancia_total=distancia_total
    )
    detalles_data = []
    for idx, punto in enumerate(orden_visita_puntos, start=1):
        detalles_data.append(DetalleRutaCreate(
            orden=idx,
            id_punto=punto['id_punto'],
            tiempo_estimado_punto=None,
            id_ruta=0
        ))
    pasos_por_detalle = []
    idx_coord = 0
    for i in range(len(orden_visita_coords) - 1):
        origen = orden_visita_coords[i]
        destino = orden_visita_coords[i + 1]
        segmento = []
        while idx_coord < len(coordenadas_ruta_completa):
            coord = coordenadas_ruta_completa[idx_coord]
            segmento.append(coord)
            if coord == destino:
                idx_coord += 1
                break
            idx_coord += 1
        pasos = []
        for j, (x, y) in enumerate(segmento):
            pasos.append(PasoRutaCreate(
                secuencia=j + 1,
                x=x,
                y=y,
                id_detalle_ruta=0
            ))
        pasos_por_detalle.append(pasos)
    ruta_guardada = RutaDetalladaRepository.crear_ruta_completa(
        db,
        ruta_data,
        detalles_data,
        pasos_por_detalle
    )
    return RutaOptimizadaResponse(
        id_tarea=tarea.id_tarea,
        reponedor=reponedor.nombre,
        fecha_creacion=str(tarea.fecha_creacion),
        puntos_reposicion=puntos_ordenados,
        coordenadas_ruta=coordenadas_respuesta,
        algoritmo_utilizado=algoritmo_info,
        distancia_total=distancia_total,
        tiempo_estimado_minutos=tiempo_estimado,
        estado_tarea=estado_nombre
    )
