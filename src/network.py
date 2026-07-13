from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from src.zone import Zone
from src.connection import Connection


class Network(BaseModel):
    """Represents the graph of zones and connections.

    The network is the core data structure that holds all zones (nodes)
    and connections (edges). It provides methods to query neighbors,
    retrieve connections, and validate the graph structure.

    Attributes:
        start_zone: The origin zone where all drones begin.
        end_zone: The destination zone where drones must arrive.
        zones: Dictionary mapping zone names to Zone objects.
        conn: Dictionary mapping normalized keys to Connection objects.
    """

    model_config = ConfigDict(frozen=False, validate_assignment=False)

    start_zone: Zone
    end_zone: Zone
    zones: dict[str, Zone] = Field(default_factory=dict)
    conn: dict[tuple[str, str], Connection] = Field(default_factory=dict)

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the network.

        Args:
            zone: The zone to add.

        Raises:
            ValueError: If a zone with the same name already exists.
        """
        if zone.name in self.zones:
            raise ValueError(
                f"Ya existe una zona con el mismo nombre: {zone.name}")
        self.zones[zone.name] = zone

    def add_connection(
            self, zone_a: Zone, zone_b: Zone, max_capacity: int = 1
    ) -> None:
        """Add a bidirectional connection between two zones.

        Args:
            zone_a: First zone of the connection.
            zone_b: Second zone of the connection.
            max_capacity: Maximum drones that can traverse simultaneously.

        Raises:
            ValueError: If either zone does not exist or if the
                connection already exists.
        """
        if zone_a.name not in self.zones:
            raise ValueError(f"'{zone_a.name}' no existe en la red")
        if zone_b.name not in self.zones:
            raise ValueError(f"'{zone_b.name}' no existe en la red")

        key = self._normalize_connection_key(zone_a.name, zone_b.name)

        if key in self.conn:
            raise ValueError(
                f"Ya existe una conexion entre '{zone_a.name}'-'{zone_b.name}'"
            )

        current_zone_a = self.zones[zone_a.name]
        current_zone_b = self.zones[zone_b.name]

        conn = Connection(
            zone_a=current_zone_a,
            zone_b=current_zone_b,
            max_capacity=max_capacity
        )
        self.conn[key] = conn

    def get_zone(self, name: str) -> Optional[Zone]:
        """Retrieve a zone by its name.

        Args:
            name: The name of the zone to find.

        Returns:
            The Zone object, or None if not found.
        """
        return self.zones.get(name)

    def get_neighbors(self, zone: Zone) -> list[Zone]:
        """Get all zones directly connected to the given zone.

        Args:
            zone: The zone whose neighbors to find.

        Returns:
            List of adjacent Zone objects.
        """
        neighbors: list[Zone] = []
        for _key, connection in self.conn.items():
            if connection.zone_a == zone:
                neighbors.append(connection.zone_b)
            elif connection.zone_b == zone:
                neighbors.append(connection.zone_a)
        return neighbors

    def get_connection(
            self, zone_a: Zone, zone_b: Zone
    ) -> Optional[Connection]:
        """Get the connection between two zones.

        Args:
            zone_a: First zone.
            zone_b: Second zone.

        Returns:
            The Connection object, or None if no connection exists.
        """
        key = self._normalize_connection_key(zone_a.name, zone_b.name)
        return self.conn.get(key)

    def get_connection_count(self) -> int:
        """Get the total number of connections in the network.

        Returns:
            Count of connections.
        """
        return len(self.conn)

    def get_all_zones(self) -> list[Zone]:
        """Get all zones in the network.

        Returns:
            List of all Zone objects.
        """
        return list(self.zones.values())

    def get_all_connections(self) -> list[Connection]:
        """Get all connections in the network.

        Returns:
            List of all Connection objects.
        """
        return list(self.conn.values())

    def get_zone_count(self) -> int:
        """Get the total number of zones in the network.

        Returns:
            Count of zones.
        """
        return len(self.zones)

    def validate_network(self) -> bool:
        """Validate the network structure and connectivity.

        Checks that start and end zones exist, are accessible,
        and that no connections involve blocked zones.

        Returns:
            True if the network is valid.

        Raises:
            ValueError: If any validation check fails.
        """
        if self.start_zone.name not in self.zones:
            raise ValueError(
                f"{self.start_zone.name} no esta en la red de zonas")
        if self.end_zone.name not in self.zones:
            raise ValueError(
                f"{self.end_zone.name} no esta en la red de zonas")

        if not self.start_zone.is_accesible():
            raise ValueError("start_zone no puede estar bloqueada")
        if not self.end_zone.is_accesible():
            raise ValueError("end_zone no puede estar bloqueada")

        for conn in self.get_all_connections():
            if conn.zone_a is None or conn.zone_b is None:
                raise ValueError(f"Conexion con zona None: {conn}")
            if (not conn.zone_a.is_accesible()
                    or not conn.zone_b.is_accesible()):
                raise ValueError(
                    f"Conexion {conn.zone_a.name}-{conn.zone_b.name} "
                    "conecta a una zona BLOCKED"
                )

        return True

    def reset_occupancy(self) -> None:
        """Reset all zone and connection occupancy to zero."""
        for zone in self.get_all_zones():
            zone.current_occupancy = 0
        for conn in self.get_all_connections():
            conn.current_occupancy = 0

    @staticmethod
    def _normalize_connection_key(
        zone_a: str,
        zone_b: str,
    ) -> tuple[str, str]:
        """Create a normalized key for bidirectional connections.

        Args:
            zone_a: Name of the first zone.
            zone_b: Name of the second zone.

        Returns:
            Tuple with zone names in alphabetical order.
        """
        if zone_a <= zone_b:
            return zone_a, zone_b
        return zone_b, zone_a
