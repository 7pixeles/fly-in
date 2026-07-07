from models import Zone, Network
from utils.exceptions import DijkstraError


def dijkstra(
        network: Network,
        start_zone: Zone,
        end_zone: Zone,
        bloqued_zone: set[str] | None = None) -> list[Zone]:
    """
    Encuentra el camino más corto entre dos zonasusando el algoritmo de
    Dijkstra.

    Parámetros:
        - network: La red de zonas y conexiones.
        - start_zone: La zona de inicio.
        - end_zone: La zona de destino.
        - bloqued_zone: Un conjunto de nombres de zonas que
                        deben ser ignoradas en la búsqueda.

    Returns:
        - Una lista de zonas que representan el camino más corto desde
          start_zone hasta end_zone. Si no hay un camino posible,
          devuelve una lista vacía.

    Raises:
        - DijkstraError: Si no se puede encontrar un camino entre
                            start_zone y end_zone.
    """

    if bloqued_zone is None:
        bloqued_zone = set()

    # Validar entrada
    if not start_zone.is_accesible():
        raise DijkstraError(
            f"La zona de inicio '{start_zone.name}' no es accesible.")
    if not end_zone.is_accesible():
        raise DijkstraError(
            f"La zona de destino '{end_zone.name}' no es accesible.")
    if start_zone.name in bloqued_zone:
        raise DijkstraError(
            f"La zona de inicio '{start_zone.name}' está bloqueada.")
    if end_zone.name in bloqued_zone:
        raise DijkstraError(
            f"La zona de destino '{end_zone.name}' está bloqueada.")

    # Inicializar estructuras de datos
    distances: dict[str, float] = {}
    previous: dict[str, str | None] = {}
    unvisited: set[str] = set()

    for zone in network.get_all_zones():
        # Ignorar zonas bloqueadas
        if zone.name in bloqued_zone:
            continue
        # Ignorar zonas inaccesibles (BLOCKED)
        if not zone.is_accesible():
            continue

        distances[zone.name] = float('inf')
        previous[zone.name] = None
        unvisited.add(zone.name)

    # Verificar que las zonas de inicio y destino estén en la red
    if start_zone.name not in distances:
        raise DijkstraError(
            f"La zona de inicio '{start_zone.name}' no está en la red.")
    if end_zone.name not in distances:
        raise DijkstraError(
            f"La zona de destino '{end_zone.name}' no está en la red.")

    distances[start_zone.name] = 0

    # Algoritmo de Dijkstra
    while unvisited:
        # Encontrar la zona no visitada con la distancia más corta
        current_zone_name: str | None = None
        min_distance = float('inf')

        for name in unvisited:
            if distances[name] < min_distance:
                min_distance = distances[name]
                current_zone_name = name

        # Si la mínima es infinito, no hay camino posible
        if min_distance == float('inf'):
            raise DijkstraError(
                f"No hay camino válido entre "
                f"'{start_zone.name}' y '{end_zone.name}'.")

        # Si llegamos a destino, reconstruir y retornar
        if current_zone_name == end_zone.name:
            path = []
            current_node: str | None = end_zone.name

            while current_node is not None:
                # Obtener objeto Zone correspondiente
                obj_zone = network.get_zone(current_node)

                if obj_zone is None:
                    raise DijkstraError(
                        f"Zona '{current_node}' no encontrada en la red.")

                path.append(obj_zone)
                current_node = previous[current_node]

            return path[::-1]

        # Marcar la zona actual como visitada
        assert current_zone_name is not None
        unvisited.remove(current_zone_name)
        current_zone = network.get_zone(current_zone_name)

        if current_zone is None:
            raise DijkstraError(
                f"Zona '{current_zone_name}' no encontrada en la red.")

        # Actualizar distancias de las zonas vecinas
        for neighbor in network.get_neighbors(current_zone):
            # Saltar si la zona está bloqueada
            if neighbor.name in bloqued_zone:
                continue

            # Saltar si ya fue visitado
            if neighbor.name not in unvisited:
                continue

            # Calcular costo del movimiento
            # Conexión siempre cuesta 1
            # Zona destino cuesta segú su tipo (1 o 2)
            connection_cost = 1
            zone_cost = neighbor.get_movement_cost()
            total_cost = connection_cost + zone_cost

            # Actualizar distancia si encontramos un camino más corto
            new_distance = distances[current_zone_name] + total_cost
            if new_distance < distances[neighbor.name]:
                distances[neighbor.name] = new_distance
                previous[neighbor.name] = current_zone_name

    # Si llegamos aquí, no se encontró un camino
    raise DijkstraError(
        f"No hay camino válido entre '{start_zone.name}' y '{end_zone.name}'.")


def block_route(blocked_zones: set[str], route: list[Zone]) -> None:
    """
    Marca zonas intermedias de una ruta como bloqueadas

    Obliga a futuras búsquedas de Dijskstra a ignorar estas zonas,
    forzando a encontrar un camino altarnativo.

    Parámetros:
        - blocked_zones: Conjunto (se modifica in-place)
        - route: Una lista de zonas que representan la ruta a bloquear.

    Nota:
        - No bloquea la zona de inicio ni la de destino
        (otros drones deben poder entrar y salir de ellar)
    """

    if len(route) < 3:
        # No hay zonas intermedias para bloquear
        return

    # Bloquear solo las zonas intermedias
    for zone in route[1:-1]:
        blocked_zones.add(zone.name)
