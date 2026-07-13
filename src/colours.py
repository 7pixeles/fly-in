from enum import Enum


class Color(Enum):
    """ANSI color definitions for terminal output.

    Each value is a tuple of (rgb, ansi_code) where rgb is a tuple
    of (r, g, b) values and ansi_code is the corresponding ANSI
    escape sequence for terminal coloring.
    """

    DEFAULT = ((200, 200, 200), "\033[0m")
    GREEN = ((80, 200, 120), "\033[32m")
    RED = ((220, 80, 80), "\033[31m")
    BLUE = ((80, 140, 255), "\033[34m")
    YELLOW = ((240, 220, 90), "\033[33m")
    PURPLE = ((180, 120, 255), "\033[35m")
    CRIMSON = ((220, 20, 60), "\033[38;5;197m")
    BLACK = ((0, 0, 0), "\033[30m")
    BROWN = ((165, 42, 42), "\033[33m")
    ORANGE = ((255, 165, 0), "\033[38;5;208m")
    MAROON = ((128, 0, 0), "\033[31m")
    GOLD = ((255, 215, 0), "\033[38;5;220m")
    DARKRED = ((139, 0, 0), "\033[31m")
    VIOLET = ((143, 0, 255), "\033[35m")
    RAINBOW = (None, "DYNAMIC_RAINBOW")


class DroneState(Enum):
    """Possible states of a drone during simulation.

    Attributes:
        IDLE: Drone is in start zone, not yet dispatched.
        MOVING: Drone has just arrived at a new zone this turn.
        IN_TRANSIT: Drone is traversing a connection to a restricted zone.
        DELIVERED: Drone has reached the end zone.
        WAITING: Drone is waiting for capacity to become available.
    """

    IDLE = "idle"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    WAITING = "waiting"
