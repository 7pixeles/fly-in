from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from models.zone import Zone


class Connection(BaseModel):
    """Representa una conexión bidireccional entre dos zonas.
 
    Una conexión es una arista del grafo que permite movimiento entre
    dos zonas adyacentes, con límites de capacidad.
 
    Atributos:
        zone_a: Primera zona conectada.
        zone_b: Segunda zona conectada.
        max_capacity: Máximo de drones que pueden cruzar simultáneamente (> 0).
        current_occupancy: Número actual de drones en tránsito (>= 0).
    """
    model_config = ConfigDict(frozen=False, validate_assignment=False)

    zone_a: Zone
    zone_b: Zone
    max_capacity: int = Field(default=1, gt=0)
    current_occupancy: int = Field(default=0, ge=0)

    @field_validator('zone_a', 'zone_b')
    @classmethod
    def zones_different(cls, value, info):
        if info.field_name == 'zone_b' and value == info.data.get('zone_a'):
            raise ValueError("No puedes conectar una zona consigo misma")

    def connects(self, zone_a: Zone, zone_b: Zone) -> bool:
        '''Verifica si esta conexión conecta las dos zonas dadas'''
        return ((self.zone_a == zone_a and self.zone_b == zone_b) or
                (self.zone_a == zone_b and self.zone_b == zone_a))

    def get_other_zone(self, from_zone: Zone) -> Optional[Zone]:
        """Retorna el otro extremo de la conexión.

        Args:
            from_zone: La zona de origen.

        Returns:
            La zona destino al otro extremo de la conexión.

        Raises:
            ValueError: Si from_zone no es parte de esta conexión.
        """
        if from_zone == self.zone_a:
            return self.zone_b

        elif from_zone == self.zone_b:
            return self.zone_a

        raise ValueError(f"La zona {from_zone.name} no está conectada"
                         f" por esta conexión"
                         f"({self.zone_a.name}, {self.zone_b.name})")

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
