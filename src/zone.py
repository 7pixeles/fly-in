from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ZoneType(Enum):
    """Types of zones that determine movement cost and behavior.

    Attributes:
        NORMAL: Standard zone with 1 turn movement cost.
        RESTRICTED: Dangerous zone costing 2 turns to enter.
        PRIORITY: Preferred zone costing 1 turn, prioritized in pathfinding.
        BLOCKED: Inaccessible zone that cannot be entered.
    """

    NORMAL = 1
    RESTRICTED = 2
    PRIORITY = 1
    BLOCKED = float('inf')


class Zone(BaseModel):
    """Represents a zone in the drone network graph.

    A zone is a node in the network that drones can occupy subject to
    capacity constraints. Each zone has a type that determines its
    movement cost, and an optional color for visual representation.

    Attributes:
        name: Unique identifier for the zone.
        zone_type: Determines movement cost and accessibility.
        x: X coordinate on the map grid.
        y: Y coordinate on the map grid.
        max_drones: Maximum number of drones that can occupy simultaneously.
        color: Optional color name for visual output.
        current_occupancy: Number of drones currently in this zone.
    """

    model_config = ConfigDict(frozen=False, validate_assignment=False)

    name: str
    zone_type: ZoneType
    x: int
    y: int
    max_drones: int = Field(default=1, gt=0)
    color: Optional[str] = Field(default=None)
    current_occupancy: int = Field(default=0, ge=0)

    def can_fit_drone(self) -> bool:
        """Check if the zone has capacity for another drone.

        Returns:
            True if current occupancy is below max_drones.
        """
        return self.current_occupancy < self.max_drones

    def add_drone(self) -> bool:
        """Add a drone to this zone if capacity allows.

        Returns:
            True if the drone was added, False if at capacity.
        """
        if self.can_fit_drone():
            self.current_occupancy += 1
            return True
        return False

    def remove_drone(self) -> bool:
        """Remove a drone from this zone.

        Returns:
            True if a drone was removed, False if zone was empty.
        """
        if self.current_occupancy > 0:
            self.current_occupancy -= 1
            return True
        return False

    def get_movement_cost(self) -> int:
        """Get the turn cost to enter this zone.

        Returns:
            The movement cost in turns.

        Raises:
            ValueError: If the zone is blocked (inaccessible).
        """
        if self.zone_type == ZoneType.BLOCKED:
            raise ValueError(f"Blocked Zone: {self.name}")
        cost: int = self.zone_type.value
        return cost

    def is_accesible(self) -> bool:
        """Check if drones can enter this zone.

        Returns:
            True if the zone is not blocked.
        """
        return self.zone_type != ZoneType.BLOCKED
