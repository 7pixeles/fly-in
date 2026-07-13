class ParseError(Exception):
    """Raised when the map file cannot be parsed correctly."""

    pass


class PathfindingError(Exception):
    """Raised when the pathfinding algorithm fails."""

    pass


class DijkstraError(Exception):
    """Raised when Dijkstra's algorithm cannot find a valid path."""

    pass


class SimulationError(Exception):
    """Raised when the simulation encounters a fatal condition."""

    pass
