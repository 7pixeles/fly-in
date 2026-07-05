PSEUDOCÓDIGO DEL MÓDULO PATHFINDING
---

Estructura completa del algoritmo heurístico de rutas multi-dron.
Este documento contiene el flujo lógico antes de implementación Python.
"""

---
1. DIJKSTRA: Búsqueda del camino más corto
---

función dijkstra(network: Network, zona_inicio: Zone, zona_fin: Zone, 
                 zonas_bloqueadas: conjunto = vacio) → lista[Zone]
    
    """
    Encuentra el camino más corto desde zona_inicio a zona_fin
    usando el algoritmo de Dijkstra.
    
    Parámetros:
        network: La red de zonas y conexiones
        zona_inicio: Punto de partida
        zona_fin: Destino
        zonas_bloqueadas: Conjunto de zonas a no considerar (para rutas alternativas)
    
    Retorna:
        lista[Zone]: Secuencia de zonas formando el camino
    
    Lanza excepciones:
        excepción si no existe camino válido
    """
    
    # Inicializar distancias y prioridades
    distancias = diccionario vacío
    anterior = diccionario vacío
    no_visitadas = conjunto vacío
    
    para cada zona en network.get_all_zones():
        si zona en zonas_bloqueadas:
            continuar  # Saltar zonas bloqueadas
        fin si
        
        distancias[zona] = infinito
        anterior[zona] = null
        no_visitadas.agregar(zona)
    fin para
    
    distancias[zona_inicio] = 0
    
    # Algoritmo principal
    mientras no_visitadas no está vacío:
        
        # 1. Encontrar zona no visitada con menor distancia
        zona_actual = null
        distancia_mínima = infinito
        
        para cada zona en no_visitadas:
            si distancias[zona] < distancia_mínima:
                distancia_mínima = distancias[zona]
                zona_actual = zona
            fin si
        fin para
        
        # Si la zona con menor distancia es infinito, no hay camino
        si distancia_mínima == infinito:
            lanzar excepción: "No existe camino válido"
        fin si
        
        # Si llegamos al destino, reconstruir camino
        si zona_actual == zona_fin:
            camino = lista vacía
            nodo = zona_fin
            
            mientras nodo no es null:
                camino.insertar_al_inicio(nodo)
                nodo = anterior[nodo]
            fin mientras
            
            retornar camino
        fin si
        
        no_visitadas.remover(zona_actual)
        
        # 2. Actualizar distancias a vecinos
        para cada vecino en network.get_neighbors(zona_actual):
            
            si vecino en zonas_bloqueadas:
                continuar  # Saltar vecinos bloqueados
            fin si
            
            si vecino no en no_visitadas:
                continuar  # Saltar ya visitados
            fin si
            
            # Calcular costo: conexión (1) + zona destino (1 ó 2)
            costo_conexión = 1
            costo_zona = vecino.get_movement_cost()  # 1, 2, o infinito
            costo_total = costo_conexión + costo_zona
            
            distancia_nueva = distancias[zona_actual] + costo_total
            
            si distancia_nueva < distancias[vecino]:
                distancias[vecino] = distancia_nueva
                anterior[vecino] = zona_actual
            fin si
        fin para
    fin mientras
    
    lanzar excepción: "No existe camino válido"


---
2. BLOQUEAR RUTA: Evitar rutas duplicadas
---

función bloquear_ruta(rutas_bloqueadas: conjunto, ruta: lista[Zone]) → None
    
    """
    Marca todas las zonas de una ruta como bloqueadas para futuras búsquedas.
    Esto obliga a Dijkstra a encontrar un camino alternativo.
    
    Parámetros:
        rutas_bloqueadas: Conjunto (conjunto vacío al inicio, se va llenando)
        ruta: La lista de zonas a bloquear
    """
    
    para cada zona en ruta:
        # No bloquear la zona inicial ni la final
        # porque otros drones también deben poder salir/entrar
        si zona != ruta[0] y zona != ruta[-1]:
            rutas_bloqueadas.agregar(zona)
        fin si
    fin para


---
3. EXPLORAR RUTAS: Generar 3 alternativas por dron
---

función explorar_rutas(network: Network, drones: lista[Drone]) 
    → diccionario[id_dron: lista[3 rutas]]
    
    """
    Para cada dron, calcula 3 rutas alternativas usando Dijkstra.
    La primera es la más corta, la segunda y tercera son alternativas.
    
    Retorna:
        diccionario mapeo dron_id → [ruta_A, ruta_B, ruta_C]
    """
    
    rutas_por_dron = diccionario vacío
    
    para cada dron en drones:
        rutas_alternativas = lista vacía
        zonas_bloqueadas = conjunto vacío
        
        para iteración en rango(1, 4):  # Buscar 3 rutas
            
            intentar:
                ruta = dijkstra(
                    network,
                    dron.current_zone,
                    dron.end_zone,
                    zonas_bloqueadas
                )
                rutas_alternativas.agregar(ruta)
                bloquear_ruta(zonas_bloqueadas, ruta)
            
            excepto no_existe_camino:
                # Si no hay más rutas, rellenar con la última encontrada
                si rutas_alternativas no está vacío:
                    rutas_alternativas.agregar(rutas_alternativas[-1])
                fin si
                romper
            fin intentar
        fin para
        
        # Asegurar que tenemos al menos 1 ruta
        si len(rutas_alternativas) == 0:
            lanzar excepción: f"No existe camino para dron {dron.id}"
        fin si
        
        rutas_por_dron[dron.id] = rutas_alternativas
    fin para
    
    retornar rutas_por_dron


---
4. EVALUAR ASIGNACIÓN: Simular la ejecución
---

función evaluar_asignación(asignación: diccionario, network: Network, 
                          drones: lista[Drone]) → int
    
    """
    Simula turno a turno la ejecución de una asignación de rutas.
    Es la función más crítica porque se ejecuta cientos de veces.
    
    Parámetros:
        asignación: diccionario {dron_id: ruta}
        network: Red de zonas y conexiones
        drones: Lista de drones (se copian para simular)
    
    Retorna:
        int: Número de turno en que el último dron llega
    
    Complejidad:
        O(turnos_simulación × num_drones)
        Esperado: 5-20 turnos en mapas pequeños
    """
    
    # Crear copias de drones y red para no modificar originals
    drones_simulados = copiar_drones(drones)
    network_simulada = copiar_network(network)
    
    # Asignar rutas a drones simulados
    para cada dron en drones_simulados:
        ruta = asignación[dron.id]
        dron.set_route(ruta)
    fin para
    
    turno = 0
    entregados = conjunto vacío
    iteraciones_sin_progreso = 0
    
    # Simulación
    mientras len(entregados) < len(drones_simulados):
        turno += 1
        
        # Salud mental: no simular más de X turnos
        si turno > 500:
            retornar 500  # Asignación muy mala
        fin si
        
        # PASO 1: Recolectar intentos de movimiento
        movimientos_válidos = diccionario vacío  # zona → lista de drones
        
        para cada dron en drones_simulados:
            si dron.id en entregados:
                continuar  # Ya llegó, saltar
            fin si
            
            siguiente_zona = dron.get_next_zone()
            
            si siguiente_zona es null:
                # Dron sin ruta, no debería ocurrir
                continuar
            fin si
            
            # Verificar si puede entrar a la siguiente zona
            si puede_entrar_a_zona(siguiente_zona, network_simulada, movimientos_válidos):
                si siguiente_zona no en movimientos_válidos:
                    movimientos_válidos[siguiente_zona] = lista vacía
                fin si
                movimientos_válidos[siguiente_zona].agregar(dron)
            fin si
        fin para
        
        # PASO 2: Procesar movimientos válidos
        drones_movidos = 0
        
        para cada (zona_destino, drones_a_mover) en movimientos_válidos.items():
            para cada dron en drones_a_mover:
                
                # Remover del zona anterior
                red_simulada.zonas[dron.current_zone.name].remove_drone()
                
                # Mover dron
                dron.advance_position(zona_destino)
                
                # Agregar a zona nueva
                red_simulada.zonas[zona_destino.name].add_drone()
                
                drones_movidos += 1
                
                # Verificar si llegó
                si dron.current_zone == dron.end_zone:
                    entregados.agregar(dron.id)
                fin si
            fin para
        fin para
        
        # PASO 3: Detectar si hay progreso
        si drones_movidos == 0:
            iteraciones_sin_progreso += 1
            
            # Si 10 turnos sin movimiento: deadlock
            si iteraciones_sin_progreso > 10:
                retornar 500  # Penalizar fuerte
            fin si
        sino:
            iteraciones_sin_progreso = 0
        fin si
    fin mientras
    
    retornar turno


función puede_entrar_a_zona(zona: Zone, network: Network, 
                            movimientos_ya_planeados: diccionario) → booleano
    
    """
    Verifica si un dron puede entrar a una zona considerando:
    1. La zona es accesible (no BLOCKED)
    2. La zona tiene capacidad disponible
    3. Los movimientos planeados en este turno respetan la capacidad
    
    Parámetros:
        zona: Zona destino
        network: Red (para acceder a estados)
        movimientos_ya_planeados: Movimientos a otra zona en este turno
    
    Retorna:
        booleano: True si puede entrar
    """
    
    # 1. ¿Es accesible?
    si no zona.is_accessible():
        retornar falso
    fin si
    
    # 2. ¿Tiene ocupancia en la red?
    ocupancia_actual = red_simulada.zonas[zona.name].current_occupancy
    
    # 3. ¿Cuántos drones intentan entrar en este turno?
    drones_entrando_este_turno = 0
    si zona en movimientos_ya_planeados:
        drones_entrando_este_turno = len(movimientos_ya_planeados[zona])
    fin si
    
    # 4. Verificar capacidad total
    ocupancia_post_movimiento = ocupancia_actual + drones_entrando_este_turno + 1
    
    si ocupancia_post_movimiento > zona.max_drones:
        retornar falso
    fin si
    
    retornar verdadero


---
5. BÚSQUEDA LOCAL ITERATIVA
---

función buscar_localmente(rutas_por_dron: diccionario, network: Network,
                         drones: lista[Drone]) 
    → (mejor_asignación: diccionario, mejor_turno: int)
    
    """
    Realiza ~100-500 iteraciones de búsqueda local (hill climbing con aceptación
    probabilística) para encontrar la mejor asignación de rutas.
    
    Parámetros:
        rutas_por_dron: {dron_id: [ruta_A, ruta_B, ruta_C]}
        network: Red para evaluaciones
        drones: Lista de drones
    
    Retorna:
        (mejor_asignación, turno_final)
    """
    
    # Crear asignación inicial: todos en su mejor ruta
    asignación_actual = crear_asignación_inicial(rutas_por_dron)
    
    mejor_asignación = copiar_diccionario(asignación_actual)
    mejor_turno = evaluar_asignación(asignación_actual, network, drones)
    
    # Parámetros de búsqueda
    iteraciones_máx = 500
    sin_mejora_máx = 100
    iteración = 0
    sin_mejora = 0
    
    mientras iteración < iteraciones_máx:
        iteración += 1
        sin_mejora += 1
        
        # PASO 1: Seleccionar dron aleatorio
        dron_id = seleccionar_id_dron_aleatorio(drones)
        
        # PASO 2: Seleccionar ruta alternativa
        rutas_disponibles = rutas_por_dron[dron_id]
        ruta_actual = asignación_actual[dron_id]
        ruta_nueva = seleccionar_ruta_diferente(rutas_disponibles, ruta_actual)
        
        # Si es la misma ruta (no hay alternativa), reintentar
        si ruta_nueva == ruta_actual:
            continuar
        fin si
        
        # PASO 3: Crear asignación temporal con cambio
        asignación_temporal = copiar_diccionario(asignación_actual)
        asignación_temporal[dron_id] = ruta_nueva
        
        # PASO 4: Evaluar
        turno_temporal = evaluar_asignación(asignación_temporal, network, drones)
        
        # PASO 5: Aceptar o rechazar
        si turno_temporal < mejor_turno:
            # Mejora encontrada: aceptar siempre
            mejor_asignación = copiar_diccionario(asignación_temporal)
            mejor_turno = turno_temporal
            asignación_actual = copiar_diccionario(asignación_temporal)
            sin_mejora = 0
        
        sino:
            # No hay mejora: aceptar con probabilidad baja
            probabilidad = calcular_probabilidad(iteración, iteraciones_máx)
            
            si número_aleatorio() < probabilidad:
                asignación_actual = copiar_diccionario(asignación_temporal)
            fin si
        fin si
        
        # PASO 6: Criterio de parada
        si sin_mejora >= sin_mejora_máx:
            romper
        fin si
    fin mientras
    
    retornar mejor_asignación, mejor_turno


función crear_asignación_inicial(rutas_por_dron: diccionario) → diccionario
    
    """
    Asignación inicial: cada dron en su primera ruta (la más corta).
    """
    
    asignación = diccionario vacío
    
    para cada (dron_id, rutas) en rutas_por_dron.items():
        asignación[dron_id] = rutas[0]  # Primera ruta (índice 0)
    fin para
    
    retornar asignación


función seleccionar_ruta_diferente(rutas: lista[3], actual: lista[Zone]) 
    → lista[Zone]
    
    """
    De las 3 rutas disponibles, selecciona una que no sea la actual.
    Aleatoriamente, sin ponderación.
    """
    
    alternativas = lista vacía
    
    para cada ruta en rutas:
        si ruta != actual:
            alternativas.agregar(ruta)
        fin si
    fin para
    
    si len(alternativas) == 0:
        retornar actual  # No hay alternativas, retornar la misma
    fin si
    
    índice_aleatorio = número_aleatorio_entre(0, len(alternativas) - 1)
    retornar alternativas[índice_aleatorio]


función calcular_probabilidad(iteración: int, iteraciones_máx: int) → float
    
    """
    Calcula probabilidad de aceptar un movimiento que no mejora.
    Usa enfoque de simulated annealing: probabilidad decrece con iteraciones.
    
    Comienza al 30% y disminuye linealmente a 0%.
    """
    
    temperatura = 1.0 - (iteración / iteraciones_máx)
    probabilidad = 0.30 * temperatura
    
    retornar máximo(probabilidad, 0.0)


---
6. REFINAMIENTO DE CONFLICTOS
---

función refinar_conflictos(asignación: diccionario, network: Network,
                          drones: lista[Drone]) → int
    
    """
    Realiza una última simulación completa de la mejor asignación encontrada.
    Detecta y reporta cualquier conflicto remanente.
    
    En una versión avanzada, aquí se intentarían resolver deadlocks
    automáticamente (reordenar movimientos, insertar esperas estratégicas).
    
    Por ahora: solo simula y retorna el resultado.
    """
    
    turno_final = evaluar_asignación(asignación, network, drones)
    
    retornar turno_final


---
7. ALGORITMO PRINCIPAL
---

función encontrar_rutas_multidron(network: Network, drones: lista[Drone])
    → (drones_con_rutas: lista[Drone], turno_final: int)
    
    """
    Orquesta todo el proceso: exploración → búsqueda → refinamiento.
    
    Retorna:
        Los drones con sus rutas asignadas y el turno final estimado
    """
    
    # FASE 1: Exploración
    imprimir("Fase 1: Explorando rutas alternativas...")
    rutas_por_dron = explorar_rutas(network, drones)
    
    # FASE 2: Búsqueda local
    imprimir("Fase 2: Buscando asignación óptima (~500 iteraciones)...")
    mejor_asignación, mejor_turno = buscar_localmente(rutas_por_dron, network, drones)
    
    # FASE 3: Refinamiento
    imprimir("Fase 3: Refinando conflictos...")
    turno_final = refinar_conflictos(mejor_asignación, network, drones)
    
    # Asignar rutas a drones originales
    para cada dron en drones:
        ruta = mejor_asignación[dron.id]
        dron.set_route(ruta)
    fin para
    
    imprimir(f"Pathfinding completado: {turno_final} turnos estimados")
    
    retornar drones, turno_final


---
NOTAS SOBRE COMPLEJIDAD
---

Tiempo total estimado:

Fase 1 (Exploración):
  - 3 llamadas a Dijkstra por dron
  - Dijkstra: O((V + E) log V) donde V=zonas, E=conexiones
  - Tiempo total: O(num_drones × (V + E) log V)
  - En mapas típicos: < 1 segundo para 5 drones

Fase 2 (Búsqueda local):
  - 500 iteraciones
  - Cada iteración: O(turnos_simulación × num_drones)
  - Esperado: 500 × 20 × 5 = 50,000 evaluaciones de dron-movimiento
  - En mapas típicos: 5-10 segundos

Fase 3 (Refinamiento):
  - 1 simulación completa
  - O(turnos_final × num_drones)
  - En mapas típicos: < 1 segundo

Total esperado: 10-20 segundos en mapas medianos con 5-10 drones

Crítico optimizar:
  - evaluar_asignación(): se llama 500+ veces, debe ser rápida
  - Evitar copias innecesarias de drones y red
  - Usar estructuras de datos eficientes (diccionarios, sets)

