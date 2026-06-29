from typing import Optional, Any

from models import Zone, ZoneType, Connection, Network, Drone, DroneState
from utils import ParseError

class MapParser:
    """Parser de archivos .map para el sisteama de navegación de drones:
    
    Responsabilidades:
        - Leer y validar sintaxis de archivos .map
        - Construir Network (zonas y conexiones)
        - Crear instancias de Drone
        - Validar integridad del mapa
    """

    def __init__(self) -> None:
        """Inicializa el parser"""
        self.nb_drones: int = 0
        self.start_zone_name: Optional[str] = None
        self.end_zone_name: Optional[str] = None
        self.zones: dict[str, Zone] = {}
        self.connections_to_add: list[tuple[str, str, int]] = []
        self.line_number: int = 0

    def parse_file(self, filepath: str) -> tuple[Network, list[Drone], int]:
        """Parsea un archivo .map y retorna Network, Drones e información.

        Parámetros:
            filepath: Ruta al archivo .map

        Returns:
            Tupla (Network, lista[drones], num_drones)

        Raises:
            ParseError: Si hay error de sintaxis o semántica
            FileNotFoundError: Si el archivo no existe
        """
        try:
            with(open(filepath, "r", encoding="utf-8") as file):
                lines = file.readlines()
        except FileNotFoundError:
            raise ParseError(f"Archivo no encontrado: {filepath}")
        except IOError as error:
            raise ParseError(f"Error leyendo archivos: {error}")

        # Parseo líneas
        # enumerate() asigna un contador que se incrementa en 1 
        # a cada elemento de un iterable y ayuda a realizar un 
        # seguimiento de las iteraciones mientras recorremos el objeto
        for self.line_number, line in enumerate(lines, start=1):
            self._process_line(line.strip())

        # Validar integridad
        self._validate_parsing()

        # Construir Network
        network = self._build_network()

        drones = self._create_drones(network)

        return network, drones, self.nb_drones
        
    def _process_line(self, line: str) -> None:
        """Procesa una línea del archivo

        Parámetros:
            line: línea a procesar (sin espacios al inicio / final)
        """

        # Ignoramos líneas vacías y comentarios
        if not line or line.startswith("#"):
            return
    
        # Procesar por tipo de línea
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
                f"Línea {self.line_number}: formato desconocido: {line}")

    def _parse_nb_drones(self, line: str) -> None:
        """
        Formato: nb_drones: <positive_integer>
        
        Raise:
            ParseError: Si formato es inválido o número <= 0
        """
        parts = line.split(":")
        try:
            nb_drones = int(parts[1].strip())
        except ValueError:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Formato inválido en nb_drones: {line}")
        if nb_drones <= 0:
            raise ParseError(
                f"Línea {self.line_number}: nb_drones debe ser > 0; "
                f"recibido: {self.nb_drones}"
            )

    def _parse_start_hub(self, line: str) -> None:
        """ Formato: start_hub: <name> <x> <y> [metadadta] """
        if self.start_zone_name is not None:
            raise ParseError(f"Línea {self.line_number}: "
                             "Ya hay un start_hub definido")
    
        zone = self._parse_zone_definition(line, "start_hub")
        self.start_zone_name = zone.name
        self.zones[zone.name] = zone

    def _parse_end_hub(self, line: str) -> None:
        """ Formato: end_hub: <name> <x> <y> [metadadta] """
        if self.end_zone_name is not None:
            raise ParseError(f"Línea {self.line_number}: "
                             "Ya hay un end_hub definido")
    
        zone = self._parse_zone_definition(line, "end_hub")
        self.end_zone_name = zone.name
        self.zones[zone.name] = zone

    def _parse_hub(self, line: str) -> None:
        """ Formato: hub: <name> <x> <y> [metadadta] """

        zone = self._parse_zone_definition(line, "hub")
        if zone.name in self.zones:
            raise ParseError(
                f"Línea {self.line_number}: Zona '{zone.name}' ya existe")
        self.zones[zone.name] = zone

    def _parse_connection_hub(self, line: str) -> None:
        """Formato: connection: <zone_1>-<zone_2> [max_link_capacity]=<n>
        
        Raises:
            ParseError: Si formato es inválido
        """
        content = line[len("connection:"):].strip()

        # Valida que content no esté vacío
        if not content:
            raise ParseError(
                f"Línea {self.line_number}: connection vacío en {line}"
            )

        # Separa por guión
        if "-" not in content:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Falta guión separador en connection: {line}")

        parts = content.split("-", 1)

        zone_a_name = parts[0].strip()

        # Valida que zone_a_name no esté vacío
        if not zone_a_name:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Nombre de zona A vacío en connection: {line}")

        # Valida que zone_a no contenga espacios
        if " " in zone_a_name or "\t" in zone_a_name:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Nombre de zona A contiene espacios: {zone_a_name}")

        rest = parts[1].strip()

        # Buscar el nombre de zona_b (el primer espacio separa de metadata)
        if " " in rest:
            part_rest = rest.split[None, 1]
            zone_b_name = part_rest[0]
            metadata_str = part_rest[1].strip()
        else:
            zone_b_name = rest
            metadata_str = ""

        # Validar que el zone_b_name no esté vacío
        if not zone_b_name:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Nombre de zona B vacío en connection: {line}")

        # Validar que zone_b_name no contenga espacios
        if " " in zone_b_name or "\t" in zone_b_name:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Nombre de zona B vacío contiene espacios: {zone_b_name}")
        
        # Validar que zone_a_name y zone_b_name no sean iguales
        if zone_a_name == zone_b_name:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Una zona no puede conectarse consigo misma "
                f"{zone_a_name}-{zone_b_name}")
        
        # Parsear metadadta
        metadata = self._parse_metadata(metadata_str)
        max_capacity = metadata.get("max_link_capacity", 1)

        # Validar max_capacity
        if not isinstance(max_capacity, (int, float) or max_capacity <= 0):
            raise ParseError(
                f"Línea {self.line_number}: "
                f"max_link_capacity debe ser un número positivo; "
                f"recibido {max_capacity}")

        # Registrar para agregar después (cuando todas las zonas existan)
        self.connections_to_add.append(
            (zone_a_name, zone_b_name, max_capacity))
        
    def _parse_metadata(self, metadata_str: str)-> dict[str, Any]:
        pass
    
    def _parse_zone_definition(self, line: str, prefix: str) -> Zone:
        pass

    def _validate_parsing(self) -> None:
        pass

    def _buid_network(self) -> Network:
        pass

    def _create_drones(self, network: Network) -> list[Drone]:
        pass