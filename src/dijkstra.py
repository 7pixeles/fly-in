from src.zone import Zone
from src.network import Network
from src.exceptions import DijkstraError


def dijkstra(
        network: Network,
        start_zone: Zone,
        end_zone: Zone,
        blocked_zones: set[str] | None = None,
        usage: dict[str, int] | None = None) -> list[Zone]:
    """Find the shortest path between two zones using Dijkstra's algorithm.

    The cost function combines connection cost (1), destination zone
    movement cost, and a usage penalty to distribute drones across
    multiple paths and avoid congestion.

    Args:
        network: The network graph to search.
        start_zone: The zone to start from.
        end_zone: The destination zone.
        blocked_zones: Optional set of zone names to exclude from search.
        usage: Optional dict tracking how many drones already use each
            zone, adding a penalty to crowded zones.

    Returns:
        Ordered list of Zone objects from start to end (inclusive).

    Raises:
        DijkstraError: If start or end zone is inaccessible, blocked,
            or if no path exists between them.
    """
    if blocked_zones is None:
        blocked_zones = set()
    if usage is None:
        usage = {}

    if not start_zone.is_accesible():
        raise DijkstraError(
            f"La zona de inicio '{start_zone.name}' no es accesible.")
    if not end_zone.is_accesible():
        raise DijkstraError(
            f"La zona de destino '{end_zone.name}' no es accesible.")
    if start_zone.name in blocked_zones:
        raise DijkstraError(
            f"La zona de inicio '{start_zone.name}' esta bloqueada.")
    if end_zone.name in blocked_zones:
        raise DijkstraError(
            f"La zona de destino '{end_zone.name}' esta bloqueada.")

    distances: dict[str, float] = {}
    previous: dict[str, str | None] = {}
    unvisited: set[str] = set()

    for zone in network.get_all_zones():
        if zone.name in blocked_zones:
            continue
        if not zone.is_accesible():
            continue
        distances[zone.name] = float('inf')
        previous[zone.name] = None
        unvisited.add(zone.name)

    if start_zone.name not in distances:
        raise DijkstraError(
            f"La zona de inicio '{start_zone.name}' no esta en la red.")
    if end_zone.name not in distances:
        raise DijkstraError(
            f"La zona de destino '{end_zone.name}' no esta en la red.")

    distances[start_zone.name] = 0

    while unvisited:
        current_zone_name: str | None = None
        min_distance = float('inf')

        for name in unvisited:
            if distances[name] < min_distance:
                min_distance = distances[name]
                current_zone_name = name

        if min_distance == float('inf'):
            raise DijkstraError(
                f"No hay camino entre "
                f"'{start_zone.name}' y '{end_zone.name}'.")

        if current_zone_name == end_zone.name:
            path: list[Zone] = []
            current_node: str | None = end_zone.name
            while current_node is not None:
                obj_zone = network.get_zone(current_node)
                if obj_zone is None:
                    raise DijkstraError(
                        f"Zona '{current_node}' no encontrada en la red.")
                path.append(obj_zone)
                current_node = previous[current_node]
            return path[::-1]

        assert current_zone_name is not None
        unvisited.remove(current_zone_name)
        current_zone = network.get_zone(current_zone_name)

        if current_zone is None:
            raise DijkstraError(
                f"Zona '{current_zone_name}' no encontrada en la red.")

        for neighbor in network.get_neighbors(current_zone):
            if neighbor.name in blocked_zones:
                continue
            if neighbor.name not in unvisited:
                continue

            connection_cost = 1
            zone_cost = neighbor.get_movement_cost()
            usage_penalty = usage.get(neighbor.name, 0) * 0.5
            total_cost = connection_cost + zone_cost + usage_penalty

            new_distance = distances[current_zone_name] + total_cost
            if new_distance < distances[neighbor.name]:
                distances[neighbor.name] = new_distance
                previous[neighbor.name] = current_zone_name

    raise DijkstraError(
        f"No hay camino entre '{start_zone.name}' y '{end_zone.name}'.")
