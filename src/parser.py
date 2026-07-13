from typing import Optional, Any

from src.zone import Zone, ZoneType
from src.network import Network
from src.drone import Drone
from src.colours import DroneState
from src.exceptions import ParseError


class MapParser:
    """Parses map files into a Network with Drones.

    Handles the custom map format with zones, connections, metadata,
    and drone count definitions. Validates input and raises
    ParseError for any malformed content.

    Attributes:
        nb_drones: Number of drones defined in the map.
        start_zone_name: Name of the start zone.
        end_zone_name: Name of the end zone.
        zones: Parsed zones keyed by name.
        conn_to_add: Connections to be added after validation.
        line_number: Current line number being processed.
    """

    def __init__(self) -> None:
        """Initialize the parser with empty state."""
        self.nb_drones: int = 0
        self.start_zone_name: Optional[str] = None
        self.end_zone_name: Optional[str] = None
        self.zones: dict[str, Zone] = {}
        self.conn_to_add: list[tuple[str, str, int]] = []
        self.line_number: int = 0

    def parse_file(self, filepath: str) -> tuple[Network, list[Drone], int]:
        """Parse a map file and return the network, drones, and count.

        Args:
            filepath: Path to the map file to parse.

        Returns:
            Tuple of (Network, list of Drones, drone count).

        Raises:
            ParseError: If the file cannot be read or contains
                invalid syntax or structure.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except FileNotFoundError:
            raise ParseError(f"Archivo no encontrado: {filepath}")
        except IOError as error:
            raise ParseError(f"Error leyendo archivo: {error}")

        for self.line_number, line in enumerate(lines, start=1):
            self._process_line(line.strip())

        self._validate_parsing()
        network = self._build_network()
        drones = self._create_drones(network)
        return network, drones, self.nb_drones

    def _process_line(self, line: str) -> None:
        """Dispatch a single line to the appropriate handler.

        Args:
            line: Stripped line from the map file.

        Raises:
            ParseError: If the line format is not recognized.
        """
        if not line or line.startswith("#"):
            return

        if line.startswith("nb_drones:"):
            self._parse_nb_drones(line)
        elif line.startswith("start_hub:"):
            self._parse_start_hub(line)
        elif line.startswith("end_hub:"):
            self._parse_end_hub(line)
        elif line.startswith("hub:"):
            self._parse_hub(line)
        elif line.startswith("connection:"):
            self._parse_connection_line(line)
        else:
            raise ParseError(
                f"Linea {self.line_number}: formato desconocido: {line}")

    def _parse_nb_drones(self, line: str) -> None:
        """Parse the nb_drones directive.

        Args:
            line: The line containing 'nb_drones: <number>'.

        Raises:
            ParseError: If the value is missing or not a positive integer.
        """
        parts = line.split(":")
        try:
            nb_drones = int(parts[1].strip())
        except ValueError:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Formato invalido en nb_drones: {line}")

        if nb_drones <= 0:
            raise ParseError(
                f"Linea {self.line_number}: nb_drones debe ser > 0; "
                f"recibido: {nb_drones}")
        self.nb_drones = nb_drones

    def _parse_start_hub(self, line: str) -> None:
        """Parse the start_hub zone definition.

        Args:
            line: The line defining the start zone.

        Raises:
            ParseError: If start_hub is defined more than once.
        """
        if self.start_zone_name is not None:
            raise ParseError(
                f"Linea {self.line_number}: Ya hay un start_hub definido")
        zone = self._parse_zone_definition(line, "start_hub:")
        self.start_zone_name = zone.name
        self.zones[zone.name] = zone

    def _parse_end_hub(self, line: str) -> None:
        """Parse the end_hub zone definition.

        Args:
            line: The line defining the end zone.

        Raises:
            ParseError: If end_hub is defined more than once.
        """
        if self.end_zone_name is not None:
            raise ParseError(
                f"Linea {self.line_number}: Ya hay un end_hub definido")
        zone = self._parse_zone_definition(line, "end_hub:")
        self.end_zone_name = zone.name
        self.zones[zone.name] = zone

    def _parse_hub(self, line: str) -> None:
        """Parse a regular hub zone definition.

        Args:
            line: The line defining a hub zone.

        Raises:
            ParseError: If a zone with the same name already exists.
        """
        zone = self._parse_zone_definition(line, "hub:")
        if zone.name in self.zones:
            raise ParseError(
                f"Linea {self.line_number}: Zona '{zone.name}' ya existe")
        self.zones[zone.name] = zone

    def _parse_connection_line(self, line: str) -> None:
        """Parse a connection definition line.

        Args:
            line: The line defining a connection between two zones.

        Raises:
            ParseError: If the format is invalid, zone names contain
                dashes or spaces, or self-connection is attempted.
        """
        content = line[len("connection:"):].strip()

        if not content:
            raise ParseError(
                f"Linea {self.line_number}: connection vacio en {line}")

        if "-" not in content:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Falta guion separador en connection: {line}")

        parts = content.split("-", 1)
        zone_a_name = parts[0].strip()

        if not zone_a_name:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Nombre de zona A vacio en connection: {line}")

        if " " in zone_a_name or "\t" in zone_a_name:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Nombre de zona A contiene espacios: {zone_a_name}")

        rest = parts[1].strip()

        if " " in rest:
            part_rest = rest.split(None, 1)
            zone_b_name = part_rest[0]
            metadata_str = part_rest[1].strip()
        else:
            zone_b_name = rest
            metadata_str = ""

        if not zone_b_name:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Nombre de zona B vacio en connection: {line}")

        if " " in zone_b_name or "\t" in zone_b_name:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Nombre de zona B contiene espacios: {zone_b_name}")

        if zone_a_name == zone_b_name:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Una zona no puede conectarse consigo misma "
                f"{zone_a_name}-{zone_b_name}")

        metadata = self._parse_metadata(metadata_str)
        max_capacity = int(metadata.get("max_link_capacity", 1))

        if max_capacity <= 0:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"max_link_capacity debe ser un numero positivo; "
                f"recibido {max_capacity}")

        self.conn_to_add.append(
            (zone_a_name, zone_b_name, max_capacity))

    def _parse_metadata(self, metadata_str: str) -> dict[str, Any]:
        """Parse a metadata string enclosed in brackets.

        Args:
            metadata_str: The content inside [...] brackets.

        Returns:
            Dictionary of parsed key-value pairs.

        Raises:
            ParseError: If the syntax is invalid or unknown keys
                are encountered.
        """
        if not metadata_str:
            return {}

        metadata: dict[str, Any] = {}
        content = metadata_str.strip()
        if content.startswith("["):
            content = content[1:]
        if content.endswith("]"):
            content = content[:-1]

        tokens = content.split()

        for token in tokens:
            if "=" not in token:
                raise ParseError(
                    f"Linea {self.line_number}: "
                    f"par clave=valor mal formado: {token}")

            key, _, value = token.partition("=")

            if not key:
                raise ParseError(
                    f"Linea {self.line_number}: "
                    f"Clave no existe para el valor {value}")

            for c in key:
                if not (c.isalpha() or c.isdigit() or c == "_"):
                    raise ParseError(
                        f"Linea {self.line_number}: "
                        f"caracter invalido en clave {key}: '{c}'")

            if not value:
                raise ParseError(
                    f"Linea {self.line_number}: "
                    f"Valor vacio para la clave {key}")

            for v in value:
                if v in ("[", "]"):
                    raise ParseError(
                        f"Linea {self.line_number}: "
                        f"'[' o ']' inesperado en valor: {value}")

            if key == "zone":
                try:
                    metadata["zone_type"] = ZoneType[value.upper()]
                except KeyError:
                    raise ParseError(
                        f"Linea {self.line_number}: "
                        f"Tipo de zona desconocido {value}")
            elif key == "color":
                metadata["color"] = value
            elif key == "max_drones":
                try:
                    max_drones = int(value)
                    if max_drones <= 0:
                        raise ValueError
                    metadata["max_drones"] = max_drones
                except ValueError:
                    raise ParseError(
                        f"Linea {self.line_number}: "
                        f"max_drones debe ser > 0: {value}")
            elif key == "max_link_capacity":
                try:
                    max_cap = int(value)
                    if max_cap <= 0:
                        raise ValueError
                    metadata["max_link_capacity"] = max_cap
                except ValueError:
                    raise ParseError(
                        f"Linea {self.line_number}: "
                        f"max_capacity debe ser > 0: {value}")
            else:
                raise ParseError(
                    f"Linea {self.line_number}: "
                    f"Clave desconocida en metadata: {key}")

        return metadata

    def _parse_zone_definition(self, line: str, prefix: str) -> Zone:
        """Parse a zone definition line with coordinates and metadata.

        Args:
            line: The full zone definition line.
            prefix: The prefix used ('start_hub:', 'end_hub:', or 'hub:').

        Returns:
            The parsed Zone object.

        Raises:
            ParseError: If arguments are missing, coordinates are
                invalid, or the zone name contains dashes.
        """
        content = line[len(prefix):].strip()
        parts = content.split(maxsplit=3)

        if len(parts) < 3:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Faltan argumentos en definicion de zona: {line}")

        name = parts[0]
        x_str = parts[1]
        y_str = parts[2]
        metadata_str = parts[3] if len(parts) == 4 else ""

        if "-" in name:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Nombre de zona no puede contener guiones: {name}")

        try:
            x = int(x_str)
            y = int(y_str)
        except ValueError:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Coordenadas deben ser enteros: {x_str}, {y_str}")

        metadata = self._parse_metadata(metadata_str)

        is_hub = prefix in ("start_hub:", "end_hub:")
        if is_hub:
            max_drones = self.nb_drones
        else:
            max_drones = metadata.get("max_drones", 1)

        try:
            zone = Zone(
                name=name,
                zone_type=metadata.get("zone_type", ZoneType.NORMAL),
                x=x,
                y=y,
                max_drones=max_drones,
                color=metadata.get("color")
            )
        except Exception as error:
            raise ParseError(
                f"Linea {self.line_number}: "
                f"Error creando zona '{name}': {error}")

        return zone

    def _validate_parsing(self) -> None:
        """Validate the completeness and consistency of parsed data.

        Raises:
            ParseError: If start_hub or end_hub is missing, drone
                count is invalid, zones in connections don't exist,
                or duplicate connections are found.
        """
        if self.start_zone_name is None:
            raise ParseError("No se definio start_hub en el mapa")
        if self.end_zone_name is None:
            raise ParseError("No se definio end_hub en el mapa")
        if self.nb_drones <= 0:
            raise ParseError("No se definio nb_drones en el mapa")
        if self.start_zone_name == self.end_zone_name:
            raise ParseError(
                "start_hub y end_hub deben ser zonas distintas")

        for zone_a, zone_b, _ in self.conn_to_add:
            if zone_a not in self.zones:
                raise ParseError(
                    f"Zona '{zone_a}' en connection no existe")
            if zone_b not in self.zones:
                raise ParseError(
                    f"Zona '{zone_b}' en connection no existe")

        seen_connections: set[tuple[str, str]] = set()
        for zone_a, zone_b, _ in self.conn_to_add:
            connection_key = (min(zone_a, zone_b), max(zone_a, zone_b))
            if connection_key in seen_connections:
                raise ParseError(
                    f"Conexion duplicada: '{zone_a}' - '{zone_b}'")
            seen_connections.add(connection_key)

    def _build_network(self) -> Network:
        """Build a Network from the parsed zones and connections.

        Returns:
            The constructed Network object.

        Raises:
            ParseError: If required zones are missing or the
                network fails validation.
        """
        try:
            if self.start_zone_name is None or self.end_zone_name is None:
                raise ParseError("Falta start_hub o end_hub")

            start = self.zones[self.start_zone_name]
            end = self.zones[self.end_zone_name]
            network = Network(start_zone=start, end_zone=end)

            for zone in self.zones.values():
                network.add_zone(zone)

            for zone_a_name, zone_b_name, max_capacity in self.conn_to_add:
                zone_a = self.zones[zone_a_name]
                zone_b = self.zones[zone_b_name]
                network.add_connection(zone_a, zone_b, max_capacity)

            network.validate_network()
            return network

        except ParseError:
            raise
        except Exception as error:
            raise ParseError(f"Error construyendo Network: {error}")

    def _create_drones(self, network: Network) -> list[Drone]:
        """Create drone instances positioned at the start zone.

        Args:
            network: The network containing start and end zones.

        Returns:
            List of Drone objects, one per nb_drones.
        """
        drones: list[Drone] = []
        start = network.start_zone
        end = network.end_zone

        for i in range(1, self.nb_drones + 1):
            drone = Drone(
                id=i,
                current_zone=start,
                start_zone=start,
                end_zone=end,
                state=DroneState.IDLE
            )
            drones.append(drone)

        return drones


def parse_map(filepath: str) -> tuple[Network, list[Drone], int]:
    """Parse a map file and return the network with drones.

    Convenience function that creates a MapParser and processes
    the given file.

    Args:
        filepath: Path to the map file.

    Returns:
        Tuple of (Network, list of Drones, drone count).

    Raises:
        ParseError: If parsing fails for any reason.
    """
    parser = MapParser()
    return parser.parse_file(filepath)
