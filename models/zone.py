from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from models.enums import ZoneType


class Zone(BaseModel):
    """Modelo de Zona para el sistema de enrutamiento de drones.

    Atributos:
        name: Identificador único de la zona.
        zone_type: Tipo de zona (NORMAL, RESTRICTED, PRIORITY, BLOCKED).
        x: Coordenada X (>= 0).
        y: Coordenada Y (>= 0).
        max_drones: Capacidad máxima de drones simultáneos (> 0).
        color: Identificador de color para visualización (opcional).
        current_occupancy: Número actual de drones en esta zona (>= 0).
    """

    model_config = ConfigDict(frozen=False, validate_assignment=False)

    name: str
    zone_type: ZoneType
    x: int = Field(ge=0, description="Coordenada X no puede ser negativa")
    x: int = Field(ge=0, description="Coordenada Y no puede ser negativa")
    max_drones: int = Field(
        default=1, gt=0, description="Capacidad máxima debe ser > 0"
    )
    color: Optional[str] = Field(
        default=None, description="Color para visualización"
    )
    current_occupancy: int = Field(
        default=0, ge=0, description="Ocupación actual debe ser >= 0"
    )

    @field_validator('current_occupancy')
    @classmethod
    def occupancy_within_limmits(cls, value, info):
        """Valida que occupancy no exceda max_drones."""
        max_drones = info.data.get('max_drones', 1)
        if value < 0 or value > max_drones:
            raise ValueError(
                f"La ocupación actual ({value}) "
                f"excede el máximo: {max_drones}")
        return value

    def can_fit_drone(self) -> bool:
        """Comprueba si hay espacio para otro dron en esta zona.
 
        Returns:
            True si current_occupancy < max_drones, False en caso contrario.
        """
        return self.current_occupancy < self.max_drones

    def add_drone(self) -> bool:
        """Intenta agregar un dron a esta zona.
 
        Returns:
            True si se agregó exitosamente, False si no hay espacio.
        """
        if self.can_fit_drone():
            self.current_occupancy += 1
            return True
        return False

    def remove_drone(self) -> bool:
        """Intenta remover un dron de esta zona.
 
        Returns:
            True si se removió exitosamente, False si la zona estaba vacía.
        """
        if self.current_occupancy > 0:
            self.current_occupancy -= 1
            return True
        return False

    def get_movement_cost(self) -> int:
        """Retorna el costo en turnos para entrar a esta zona.
 
        Returns:
            1 para NORMAL o PRIORITY, 2 para RESTRICTED.
 
        Raises:
            ValueError: Si la zona es BLOCKED.
        """
        if self.zone_type == ZoneType.BLOCKED:
            raise ValueError(f"Zona bloqueada: {self.name} inaccesible")
        return self.zone_type.value

    def is_accesible(self) -> bool:
        """Comprueba si esta zona es accesible para los drones.
 
        Returns:
            True si zone_type != BLOCKED, False en caso contrario.
        """
        return self.zone_type != ZoneType.BLOCKED
