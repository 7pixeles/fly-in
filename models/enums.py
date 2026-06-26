from enum import Enum


# ENUMS
class ZoneType(Enum):
    NORMAL = 1      # 1 turno de costo
    RESTRICTED = 2  # 2 turnos de costo
    PRIORITY = 1    # 1 turno pero preferido en pathfinding
    BLOCKED = None  # No se puede pasar por esta zona


class DroneState(Enum):
    IDLE = "idle"               # En una zona, esperando
    MOVING = "moving"           # Transitando entre zonas
    IN_TRANSIT = "in_transit"   # En vuelo hacia restricted (ocupando conexión)
    WAITING = "waiting"         # Bloqueaado por ocupación de zona o conexión
    DELIVERED = "delivered"     # Ha llegado a la zona final
