from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from models.zone import Zone


class Connection(BaseModel):
    '''Representa una conexión entre dos zonas'''
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
        '''Dada una zona, retorna la otra zona conectada por esta conexión'''
        if from_zone == self.zone_a:
            return self.zone_b

        elif from_zone == self.zone_b:
            return self.zone_a

        raise ValueError(f"La zona {from_zone.name} no está conectada"
                         f" por esta conexión"
                         f"({self.zone_a.name}, {self.zone_b.name})")

    def can_fit_drone(self) -> bool:
        return self.current_occupancy < self.max_capacity

    def add_drone(self) -> bool:
        if self.can_fit_drone():
            self.current_occupancy += 1
            return True

        return False

    def remove_drone(self) -> bool:
        if self.current_occupancy > 0:
            self.current_occupancy -= 1
            return True

        return False
