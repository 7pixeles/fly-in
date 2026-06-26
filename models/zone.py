from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
    # frozen=False: se pueden modificar los atributos después de instanciarlo
    # default_factory: permite asignar valores dinámicos
from models.enums import ZoneType

class Zone(BaseModel):
    model_config = ConfigDict(frozen=False, validate_assignment=False)

    name: str
    zone_type: ZoneType
    x: int = Field(default=0, ge=0)
    y: int = Field(default=0, ge=0)
    max_drones: int = Field(default=1, gt=0)
    color: Optional[str] = None
    current_occupancy: int = Field(default=0, ge=0)

    @field_validator('x', 'y')
    @classmethod
    def validate_coordinates(cls, value):
        if value < 0:
            raise ValueError("Las coordenadas deben ser no negativas")
        return value

    @field_validator('zone_type')
    @classmethod
    def validate_zone_type(cls, value):
        if not isinstance(value, ZoneType):
            raise ValueError(f"Tipo de zona inválido: {value} ")
        return value

    @field_validator('current_occupancy')
    @classmethod
    def occupancy_within_limmits(cls, value, info):
        max_drones = info.data.get('max_drones', 1)
        if value < 0 or value > max_drones:
            raise ValueError(
                f"La ocupación actual ({value}) excede el máximo: {max_drones}")
        return value


    def can_fit_drone(self) -> bool:
        '''Verifica si se puede ubicar un dron en esta zona'''
        return self.current_occupancy < self.max_drones


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


    def get_movement_cost(self) -> int:
        if self.zone_type == ZoneType.BLOCKED:
            raise ValueError(f"Zona bloqueada: {self.name} inaccesible")
        return self.zone_type.value


    def is_accesible(self) -> bool:
        return self.zone_type != ZoneType.BLOCKED
