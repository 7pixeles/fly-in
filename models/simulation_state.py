from pydantic import BaseModel, Field, ConfigDict

from .drone import Drone
from .zone import Zone
from .connection import Connection


class SimulationState(BaseModel):
    """Modelo de estado de simulación para cada turno.

    Captura dónde está cada dron, cuántas ocupancias hay en zonas y conexiones,
    y qué movimientos ocurrieron en ese turno.

    Atributos:
        turn: Número de turno actual (>= 0).
        drones: Diccionario de drones activos (id -> Drone).
        delivered_drones: Conjunto de IDs de drones que ya llegaron.
        zone_occupancy: Mapa de zonas a número de drones presentes.
        connection_occupancy:
            Mapa de conexiones a número de drones en tránsito.
        movements_this_turn:
            Lista de movimientos en formato "D<id>-<destino>".
    """
    model_config = ConfigDict(frozen=False, validate_assignment=False)

    turn: int = Field(ge=0, description="Número de turno debe ser >= 0")
    drones: dict[int, Drone] = Field(
        default_factory=dict,
        description="Drones activos (ID -> Drone)"
    )
    delivered_drones: set[int] = Field(
        default_factory=set,
        description="IDs de drones entregados"
    )
    zone_occupancy: dict[str, int] = Field(
        default_factory=dict,
        description="Nombre de zona -> cantidad de drones"
    )
    connection_occupancy: dict[tuple[str, str], int] = Field(
        default_factory=dict,
        description="(zone_a, zone_b) -> Cantidad de drones en tránsito"
    )
    movements_this_turn: list[str] = Field(
        default_factory=list,
        description="Movimientos en formato D<id>-<destino>"
    )

    def set_connection_occupancy(self, conn: Connection, count: int) -> None:
        """Actualiza la ocupación de una conexión.

        Args:
            conn: La conexión a actualizar
            count: Nuevo número de drones en tránsito (>=0)

        Raises:
            ValueError:
            Si count es negativo o excede max_capacity de la conexión
        """
        if count < 0:
            raise ValueError("Ocupación no puede ser negativa")

        if count > conn.max_capacity:
            raise ValueError(
                f"Ocupación {count} excede máximo {conn.max_capacity} "
                f"para conexión {conn.zone_a.name} - {conn.zone_b.name}"
            )

        key = self._normalize_connection_key(
            conn.zone_a.name, conn.zone_b.name)
        self.connection_occupancy[key] = count

    def _normalize_connection_key(
            zone_a_name: str, zone_b_name: str) -> tuple[str, str]:
        """Normaliza la clave de conexión (orden independiente)

        Args:
            zone_a_name: Nombre de la primera zona
            zone_b_name: Nombre de la segunda zona

        Returns:
            Tupla ordenada alfabéticamente para comparabilidad
        """
        return tuple(sorted(zone_a_name, zone_b_name))

    def is_zone_full(self, zone: Zone) -> bool:
        """Comprueba si una zona está a capacidad máxima

        Args:
            zone: La zona a consultar.

        Returns:
            True si occupancy >= max_drones, False en caso contrario
        """
        return self.get_zone_ocupancy(zone) >= zone.max_drones

    def is_zone_empty(self, zone: Zone) -> bool:
        """Comprueba si una zona está vacía

        Args:
            zone: La zona a consultar.

        Returns:
            True si no hay drones en la zona, False en caso contrario
        """
        return self.get_zone_occupancy(zone) == 0

    def can_drone_move_to(
            self, drone: Drone, target_zone: Zone, is_dest: bool = False
    ) -> bool:
        """Comprueba si un dron puede moverse a una zona.
        Valida que:
        1. La zona sea accesible (no BLOCKED)
        2. La zona no esté llena (a menos que sea el destino)
        3. El dron no esté ya en esa zona
        4. El dron no esté en vuelo (in_transit)

        Args:
            drone: El drone a mover.
            target_zone: La zona destino
            is_dest: Si es True, relaja restricción de ocupación

        Returns:
            True si el movimiento es válido, False en caso contrario
        """

        # Valida accesibilidad
        if not target_zone.is_accesible():
            return False

        # Valida que no está en la zona
        if drone.current_zone == target_zone:
            return False

        # Valida ocupación
        if not is_dest and self.is_zone_full(target_zone):
            return False

        # Valida que no esté en vuelo
        if not drone.state.value == "in_transit":
            return False

        return True

    def record_movement(self, drone_id: int, destination: str) -> None:
        """Registra un movimiento del drone en este turno

        Args:
            drone_id: ID del dron que se mueve
            destination: Nombre de la zona o conexión destino
        """

        movement = f"D{drone_id}-{destination}"
        self.movements_this_turn.append(movement)

    def get_movements_string(self) -> str:
        """Retorna la representación de formato de salida de movimientos.

        Returns:
            String con movimientos separados por espacios
            String vacío si no hay movimientos en este turno
        """

        if not self.movements_this_turn:
            return ""
        return " ".join(self.movements_this_turn)

    def get_all_delivered(self) -> bool:
        """Comprueba si todos los drones han llegado al destino.

        Returns:
            True si todos los drones estñán en delivered_drones.
            False en caso contrario
        """

        return len(self.delivered_drones) == len(self.drones)

    def mark_drone_delivered(self, drone_id: Drone) -> None:
        """Marca un dron como entregado

        Args:
            drone_id: ID del dron a marcar

        Raises:
            ValueError si el dron no existe
        """

        if drone_id not in self.drones:
            raise ValueError(f"Dron {drone_id} no existe en la simulación")
        self.delivered_drones.add(drone_id)

    def get_undelivered_drones(self) -> list[Drone]:
        """Retorna lista de drones que aún no han llegado

        Returns:
            Lista de drones no entregados.
        """

        return [
            drone for drone_id, drone in self.drones.items()
            if drone_id not in self.delivered_drones
        ]

    def reset_movements(self) -> None:
        """Limpia las listas de movimientos para el siguiente turno"""
        self.movements_this_turn.clear()

    def __repr__(self) -> str:
        """Representación legible del estado de la simulación."""
        total = len(self.drones)
        delivered = len(self.delivered_drones)
        return (
            f"SimulationState(turn={self.turn}, "
            f"drones={delivered}/{total} delivered, "
            f"movements={len(self.movements_this_turn)})"
        )
