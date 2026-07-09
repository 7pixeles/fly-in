from pydantic import BaseModel, Field, ConfigDict, field_validator

from .zone import Zone


class Connection(BaseModel):
    """Modelo de Conexión para el sistema de enrutamiento de drones.

    Atributos:
        zone_a: Primera zona conectada.
        zone_b: Segunda zona conectada.
        max_capacity: Máximo de drones que pueden cruzar simultáneamente (> 0).
        current_occupancy: Número actual de drones en tránsito (>= 0).
    """
    model_config = ConfigDict(
        frozen=False,
        validate_assignment=False,
        arbitrary_types_allowed=True)
    zone_a: Zone
    zone_b: Zone
    max_capacity: int = Field(
        default=1, gt=0, description="Capacidad máxima debe ser > 0"
    )
    current_occupancy: int = Field(
        default=0, ge=0, description="Ocupación actual debe ser >= 0"
    )

    def can_fit_drone(self) -> bool:
        """Comprueba si hay capacidad para otro dron en tránsito.

        Returns:
            True si current_occupancy < max_capacity, False en caso contrario.
        """
        return self.current_occupancy < self.max_capacity

    def add_drone(self) -> bool:
        """Intenta agregar un dron a esta conexión.

        Returns:
            True si se agregó exitosamente, False si no hay capacidad.
        """
        if self.can_fit_drone():
            self.current_occupancy += 1
            return True

        return False

    def remove_drone(self) -> bool:
        """Intenta remover un dron de esta conexión.

        Returns:
            True si se removió exitosamente, False si estaba vacía.
        """
        if self.current_occupancy > 0:
            self.current_occupancy -= 1
            return True

        return False
