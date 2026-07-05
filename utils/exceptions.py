
class ParseError(Exception):
    """Error durante el parsing de archivo .map"""
    pass


class PathfindingError(Exception):
    """Error durante la ejecución de un algoritmo de pathfinding"""
    pass


class DijkstraError(Exception):
    """Error durante la búsqueda de Dijkstra"""
    pass


class SimulationError(Exception):
    """Error durante la simulación."""
    pass

