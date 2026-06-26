from pydantic import BaseModel, Field, ConfigDict, field_validator

from models.zone import Zone
from models.connection import Connection


class Network(BaseModel):
    model_config = ConfigDict(frozen=False, validate_assignment=False)

    start_zone: Zone
    end_zone: Zone
    zones: dict[str, Zone] = Field(default_factory=dict)
    connections: dict[tuple[str, str], Connection] = Field(default_factory=dict)

    @field_validator('start_zone', 'end_zone')
    @classmethod
    def zones_differents(cls, value, info):
        if (info.field_name == 'end_zone' and value == info.data.get('start_zone')):
            raise ValueError("Start y End no pueden ser la misma zona")
        return value

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self.zones:
            raise ValueError(f"{zone.name} ya existe")
        self.zones[zone.name] = zone

    def add_connection(self, zone_a: Zone, zone_b: Zone, max_capacity: int = 1
                       ) -> None:

        if zone_a.name not in self.zones or zone_b.name not in self.zones:
            raise ValueError("Una o ambas zonas no existen")
        key = tuple(sorted([zone_a.name, zone_b.name]))
        if key in self.connections:
            raise ValueError(f"Conexión {key} ya existe")
        self.connections[key] = Connection(
            zone_a=zone_a,
            zone_b=zone_b,
            max_capacity=max_capacity
        )

    def get_neighbors(self, zone: Zone) -> list[Zone]:
        neighbors = []

        for (a, b), connection in self.connections.items():
            if connection.zone_a == zone:
                neighbors.append(connection.zone_b)
            elif connection.zone_b == zone:
                neighbors.append(connection.zone_a)
        return neighbors
