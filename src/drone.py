from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from src.colours import DroneState
from src.zone import Zone


class Drone(BaseModel):
    """Represents a drone navigating through the zone network.

    A drone follows a planned route from start to end zone, advancing
    one zone per turn (or two turns for restricted zones). It tracks
    its current position, planned route, and state.

    Attributes:
        id: Unique positive integer identifier.
        current_zone: The zone where the drone currently resides.
        start_zone: The origin zone where the drone begins.
        end_zone: The destination zone where the drone must arrive.
        planned_route: Ordered list of zones from current to end.
        state: Current state of the drone in the simulation.
        turns_in_flight: Remaining turns before reaching next zone.
    """

    model_config = ConfigDict(frozen=False, validate_assignment=False)

    id: int = Field(gt=0)
    current_zone: Zone
    start_zone: Zone
    end_zone: Zone
    planned_route: list[Zone] = Field(default_factory=list)
    state: DroneState = Field(default=DroneState.IDLE)
    turns_in_flight: int = Field(default=0, ge=0)

    def set_route(self, route: list[Zone]) -> None:
        """Set the planned route for this drone.

        Args:
            route: Ordered list of zones from current position to end.

        Raises:
            ValueError: If route does not start at current_zone
                or does not end at end_zone.
        """
        if route and route[0] != self.current_zone:
            raise ValueError(
                f"La ruta no comienza en {self.current_zone.name}")
        if route and route[-1] != self.end_zone:
            raise ValueError(f"La ruta no termina en {self.end_zone.name}")
        self.planned_route = route

    def get_next_zone(self) -> Optional[Zone]:
        """Get the next zone in the planned route.

        Returns:
            The next Zone to visit, or None if at the end of the route.
        """
        if not self.planned_route or len(self.planned_route) <= 1:
            return None
        return self.planned_route[1]

    def get_steps_remaining(self) -> int:
        """Get the number of steps left to reach the end zone.

        Returns:
            Count of remaining zones to visit in the route.
        """
        return max(0, len(self.planned_route) - 1)

    def has_route_planned(self) -> bool:
        """Check if the drone has a route assigned.

        Returns:
            True if a route has been set.
        """
        return len(self.planned_route) > 0

    def advance_position(self, next_zone: Zone) -> None:
        """Move the drone to the next zone in its route.

        Args:
            next_zone: The zone to advance to.

        Raises:
            ValueError: If the drone has no route or next_zone
                does not match the expected next position.
        """
        if not self.has_route_planned():
            raise ValueError(f"Drone {self.id} has no planned route")

        expected_next = self.get_next_zone()
        if next_zone != expected_next:
            raise ValueError(
                f"Trying to move to {next_zone.name}, "
                f"but the next step is "
                f"{expected_next.name if expected_next else 'none'}"
            )

        self.planned_route = self.planned_route[1:]
        self.current_zone = next_zone
