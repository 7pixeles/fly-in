from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from utils.enums import DroneState
from models.zone import Zone


class Drone(BaseModel):
    """Modelo de Drone para el sistema de enrutamiento de drones.

    Atributos:
        id: Identificador único del dron (> 0).
        current_zone: Zona donde se encuentra actualmente.
        start_zone: Zona de inicio (para validaciones).
        end_zone: Zona destino final.
        planned_route: Ruta planeada (lista de zonas a atravesar).
        state: Estado actual del dron (IDLE, MOVING, etc.).
        turns_in_flight:
            Turnos restantes si está en tránsito hacia zona restringida.
    """
    model_config = ConfigDict(frozen=False, validate_assignment=False)

    id: int = Field(gt=0)
    current_zone: Zone
    start_zone: Zone
    end_zone: Zone
    planned_route: list[Zone] = Field(
        default_factory=list, description="Ruta planeada del dron")
    state: DroneState = Field(default=DroneState.IDLE)
    turns_in_flight: int = Field(
        default=0, ge=0, description="Turnos restantes en vuelo")

    @field_validator('planned_route')
    @classmethod
    def route_validity(cls, value, info):
        """Valida que la ruta empiece en current_zone y termine en end_zone."""
        if not value:
            return value

        start = info.data.get('current_zone')
        end = info.data.get('end_zone')

        if start and value[0] != start:
            raise ValueError(f"La ruta debe empezar en {start.name}")
        if end and value[-1] != end:
            raise ValueError(f"La ruta debe terminar en {end.name}")
        return value

    def set_route(self, route: list[Zone]) -> None:
        """Asigna una nueva ruta al dron.

        Args:
            route: Lista de zonas a atravesar.

        Raises:
            ValueError:
            Si la ruta no empieza en current_zone o no termina en end_zone.
        """
        if route and route[0] != self.current_zone:
            raise ValueError(
                f"La ruta no comienza en {self.current_zone.name}")
        if route and route[-1] != self.end_zone:
            raise ValueError(f"La ruta no termina en {self.end_zone.name}")
        self.planned_route = route

    def get_next_zone(self) -> Optional[Zone]:
        """Retorna el siguiente destino en la ruta.

        Returns:
            La próxima zona a visitar, o None si ya no hay ruta.
        """
        if not self.planned_route or len(self.planned_route) <= 1:
            return None
        return self.planned_route[1]  # Indice 0 es donde está el drone

    def get_steps_remaining(self) -> int:
        """Cuenta cuántos movimientos faltan hasta el destino.

        Returns:
            Número de pasos restantes (len(route) - 1).
        """
        return max(0, len(self.planned_route) - 1)

    def has_route_planned(self) -> bool:
        """Comprueba si el dron tiene una ruta asignada.

        Returns:
            True si planned_route no está vacía, False en caso contrario.
        """
        return len(self.planned_route) > 0

    def advance_position(self, next_zone: Zone) -> None:
        """Mueve el dron a la siguiente zona.

        Actualiza current_zone y elimina el primer elemento de planned_route.

        Args:
            next_zone: La zona a la que moverse.

        Raises:
            ValueError: Si next_zone no es el siguiente paso en la ruta.
        """
        if not self.has_route_planned():
            raise ValueError(f"Dron {self.id} no tiene ruta planeada")

        expected_next = self.get_next_zone()
        if next_zone != expected_next:
            raise ValueError(
                f"Intento de mover a {next_zone.name}, "
                f"pero el siguiente paso es "
                f"{expected_next.name if expected_next else 'ninguno'}"
            )

        # Remover la zona actual de la ruta (ahora es la nueva zona)
        self.planned_route = self.planned_route[1:]
        self.current_zone = next_zone
