from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
    # default_factory permite asignar valores dinámicos
from models.enums import DroneState
from models.zone import Zone

class Drone(BaseModel):
    model_config = ConfigDict(frozen=False, validate_assignment=False)

    id: int = Field(gt=0)
    planned_route: list[Zone] = Field(default_factory=list)
    state: DroneState = Field(default=DroneState.IDLE)
    turns_in_flight: int = Field(default=0, ge=0)
    current_zone = Zone
    end_zone: Zone = Field(default=None) # Necesario para validar la ruta


    @field_validator('planned_route')
    @classmethod
    def route_validity(cls, value, info):
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
        if route and route[0] != self.current_zone:
            raise ValueError(f"La ruta no comienza en {self.current_zone.name}")
        if route and route[-1] != self.end_zone:
            raise ValueError(f"La ruta no termina en {self.end_zone.name}")
        self.planned_route = route


    def get_next_zone(self) -> Optional[Zone]:
        if not self.planned_route or len(self.planned_route) <= 1:
            return None

        return self.planned_route[1] # Indice 0 es donde está el drone


    def get_steps_remaining(self) -> int:
        return max(0, len(self.planned_route) - 1)


    def has_route_planned(self) -> bool:
        return len(self.planned_route) > 0
