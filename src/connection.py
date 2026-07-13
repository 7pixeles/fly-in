from pydantic import BaseModel, Field, ConfigDict

from src.zone import Zone


class Connection(BaseModel):
    """Represents a bidirectional connection between two zones.

    A connection is an edge in the network graph. It has a capacity
    that limits how many drones can traverse it simultaneously.

    Attributes:
        zone_a: First zone of the connection.
        zone_b: Second zone of the connection.
        max_capacity: Maximum drones that can traverse simultaneously.
        current_occupancy: Number of drones currently traversing.
    """

    model_config = ConfigDict(frozen=False, validate_assignment=False)

    zone_a: Zone
    zone_b: Zone
    max_capacity: int = Field(default=1, gt=0)
    current_occupancy: int = Field(default=0, ge=0)

    @property
    def name(self) -> str:
        """Return the canonical connection name (alphabetically sorted).

        Returns:
            String in the format 'zoneA-zoneB' sorted alphabetically.
        """
        names = sorted([self.zone_a.name, self.zone_b.name])
        return f"{names[0]}-{names[1]}"

    def can_fit_drone(self) -> bool:
        """Check if the connection has capacity for another drone.

        Returns:
            True if current occupancy is below max_capacity.
        """
        return self.current_occupancy < self.max_capacity

    def add_drone(self) -> bool:
        """Add a drone to this connection if capacity allows.

        Returns:
            True if the drone was added, False if at capacity.
        """
        if self.can_fit_drone():
            self.current_occupancy += 1
            return True
        return False

    def remove_drone(self) -> bool:
        """Remove a drone from this connection.

        Returns:
            True if a drone was removed, False if connection was empty.
        """
        if self.current_occupancy > 0:
            self.current_occupancy -= 1
            return True
        return False
