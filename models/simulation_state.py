from pydantic import BaseModel, Field, ConfigDict

from models.drone import Drone


class SimulationState(BaseModel):
    model_config = ConfigDict(frozen=False, validate_assignment=False)

    turn: int = Field(ge=0)
    drones: dict[int, Drone]
    zone_occupancy: dict[str, int]  # name -> count
    connection_occupancy: dict[tuple[str, str], int]
    delivered_drones: set[int] = Field(default_factory=set)
    movements_this_turn: list[str] = Field(default_factory=list)

    def record_movements(self, drone_id: int, destination: str) -> None:
        self.movements_this_turn.append(f"D{drone_id}-[destination]")

    def get_movements_string(self) -> str:
        return " ".join(self.movements_this_turn)
