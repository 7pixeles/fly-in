from typing import Optional, Any

from models import Zone, Network, Drone
from utils.exceptions import ParseError
from utils.enums import ZoneType, DroneState


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
        self.conn_to_add: list[tuple[str, str, int]] = []
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
            with (open(filepath, "r", encoding="utf-8") as file):
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
        self.nb_drones = nb_drones

    def _parse_start_hub(self, line: str) -> None:
        """ Formato: start_hub: <name> <x> <y> [metadadta] """
        if self.start_zone_name is not None:
            raise ParseError(f"Línea {self.line_number}: "
                             "Ya hay un start_hub definido")

        zone = self._parse_zone_definition(line, "start_hub:")
        self.start_zone_name = zone.name
        self.zones[zone.name] = zone

    def _parse_end_hub(self, line: str) -> None:
        """ Formato: end_hub: <name> <x> <y> [metadadta] """
        if self.end_zone_name is not None:
            raise ParseError(f"Línea {self.line_number}: "
                             "Ya hay un end_hub definido")

        zone = self._parse_zone_definition(line, "end_hub:")
        self.end_zone_name = zone.name
        self.zones[zone.name] = zone

    def _parse_hub(self, line: str) -> None:
        """ Formato: hub: <name> <x> <y> [metadadta] """

        zone = self._parse_zone_definition(line, "hub:")
        if zone.name in self.zones:
            raise ParseError(
                f"Línea {self.line_number}: Zona '{zone.name}' ya existe")
        self.zones[zone.name] = zone

    def _parse_connection_line(self, line: str) -> None:
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
            part_rest = rest.split(None, 1)
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
        max_capacity = int(metadata.get("max_link_capacity", 1))

        # Validar max_capacity
        if not isinstance(max_capacity, (int, float) or max_capacity <= 0):
            raise ParseError(
                f"Línea {self.line_number}: "
                f"max_link_capacity debe ser un número positivo; "
                f"recibido {max_capacity}")

        # Registrar para agregar después (cuando todas las zonas existan)
        self.conn_to_add.append(
            (zone_a_name, zone_b_name, max_capacity))

    def _parse_metadata(self, metadata_str: str) -> dict[str, Any]:
        """Parsea bloque de metadata
        Formato: [zone=tyoe color=value max_drones=5 ...]

        Parámetros:
            metadata_str: String entre corchetes (sin los corchetes)

        Returns:
            Diccionario con metadatos parseados

        Raises:
            ParseError: Si metadata es inválida
        """

        if not metadata_str:
            return {}

        metadata: dict[str, Any] = {}

        # Limpiar metadata_str (limpiar corchetes si los hubiera)
        content = metadata_str.strip()
        if content.startswith("["):
            content = content[1:]
        if content.endswith("]"):
            content = content[:-1]

        # Separar en tokens por espacios en blanco
        tokens = content.split()

        for token in tokens:
            # 1 Debe contener un '='
            if "=" not in token:
                raise ParseError(
                    f"Línea {self.line_number}: "
                    f"par clave=valor mal formado: {token}")

            # 2 Partir solo por el primer '='
            # (evita romperse si el valor trae otro '=')
            key, _, value = token.partition("=")

            # 3 Validar key
            if not key:
                raise ParseError(
                    f"Línea {self.line_number}: "
                    f"Clave no existe para el valor {value}")

            for c in key:
                if not (c.isalpha() or c.isdigit() or c == "_"):
                    raise ParseError(
                        f"Línea {self.line_number}: "
                        f"caracter inválido en clave {key}: '{c}'")

            # 4 Validar value
            if not value:
                raise ParseError(
                    f"Línea {self.line_number}: "
                    f"Valor vacío para la clave {key}")

            for v in value:
                if v == "[" or v == "]":
                    raise ParseError(
                        f"Línea {self.line_number}: "
                        f"'[' o ']' inesperado en valor: {value}")

            # 5. Asignar valores a cada clave
            if key == "zone":
                try:
                    metadata["zone_type"] = ZoneType[value.upper()]
                except KeyError:
                    raise ParseError(
                        f"Línea {self.line_number}: "
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
                        f"Línea {self.line_number}: "
                        f"max_drones debe ser > 0: {value}")

            elif key == "max_link_capacity":
                try:
                    max_capacity = int(value)
                    if max_capacity <= 0:
                        raise ValueError
                    metadata["max_link_capacity"] = max_capacity
                except ValueError:
                    raise ParseError(
                        f"Línea {self.line_number}: "
                        f"max_capacity debe ser > 0: {value}")

            else:
                raise ParseError(
                    f"Línea {self.line_number}: "
                    f"Clave desconocida en metadata: {key}")

        return metadata

    def _parse_zone_definition(self, line: str, prefix: str) -> Zone:
        """Parsea definición de una zona.
        Formato: <prefix>: <name> <x> <y> [metadata]

        Parámetros:
            line: línea a parsear
            prefix: (start_hub:, end_hub:, hub:)

        Returns:
            Instancia de Zone construida

        Raises:
            ParseError: Si hay error de sintaxis o semántica
        """
        # Eliminar el prefijo
        content = line[len(prefix):].strip()

        # Separar en como máximo 4 partes (name, x, y, metadata)
        parts = content.split(maxsplit=3)

        if len(parts) < 3:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Faltan argumentos en definición de zona: {line}")

        name = parts[0]
        x_str = parts[1]
        y_str = parts[2]
        metadata_str = parts[3] if len(parts) == 4 else ""

        # Validar nombre (no dashes)
        if "-" in name:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Nombre de zona no puede contener guiones: {name}")

        # Convertir coordenadas a enteros
        try:
            x = int(x_str)
            y = int(y_str)
        except ValueError:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Coordenadas deben ser enteros: {x_str}, {y_str}")

        # Parsear metadata
        metadata = self._parse_metadata(metadata_str)

        # Construir instancia de Zone
        try:
            zone = Zone(
                name=name,
                zone_type=metadata.get("zone_type", ZoneType.NORMAL),
                x=x,
                y=y,
                max_drones=metadata.get("max_drones", 1),
                color=metadata.get("color")
            )
        except Exception as error:
            raise ParseError(
                f"Línea {self.line_number}: "
                f"Error creando zona '{name}': {error}")

        return zone

    def _validate_parsing(self) -> None:
        """ Valida integraidad del mapa después de parsear todas las líneas.

        Raises:
            ParseError: Si hay inconsistencias
        """
        # Validar que start_hub y end_hub estén definidos
        if self.start_zone_name is None:
            raise ParseError("No se definió start_hub en el mapa")
        if self.end_zone_name is None:
            raise ParseError("No se definió end_hub en el mapa")

        # Validar que hay drones
        if self.nb_drones <= 0:
            raise ParseError("No se definió nb_drones en el mapa")

        # Validar que start_hub y end_hub existen en zonas distintas (otra vez)
        if self.start_zone_name == self.end_zone_name:
            raise ParseError(
                "start_hub y end_hub deben ser zonas distintas")

        # Validar que todas las zonas en conexiones existen
        for zone_a, zone_b, _ in self.conn_to_add:
            if zone_a not in self.zones:
                raise ParseError(
                    f"Zona '{zone_a}' en connection no existe")
            if zone_b not in self.zones:
                raise ParseError(
                    f"Zona '{zone_b}' en connection no existe")

        # Validar que no hay conexiones duplicadas
        seen_connections = set()
        for zone_a, zone_b, _ in self.conn_to_add:
            # Normalizar (orden independiente)
            connection_key = (
                min(zone_a, zone_b),
                max(zone_a, zone_b),
            )
            if connection_key in seen_connections:
                raise ParseError(
                    f"Conexión duplicada: '{zone_a}' - '{zone_b}'")
            seen_connections.add(connection_key)

    def _build_network(self) -> Network:
        """Construye la instancia de Network a partir de los datos parseados.

        Returns:
            Instancia de Network construida y validada

        Raises:
            ParseError: Si hay error al construir la red
        """
        try:
            # Obtener start y end
            if self.start_zone_name is None or self.end_zone_name is None:
                raise ParseError("Falta start_hub o end_hub")

            start = self.zones[self.start_zone_name]
            end = self.zones[self.end_zone_name]
            # Crear Network
            network = Network(start_zone=start, end_zone=end)

            # Agregar TODAS las zonas primero
            for zone in self.zones.values():
                network.add_zone(zone)

            # Agregar todas las conexiones al network
            for (zone_a_name, zone_b_name, max_capacity) in self.conn_to_add:
                zone_a = self.zones[zone_a_name]
                zone_b = self.zones[zone_b_name]
                network.add_connection(zone_a, zone_b, max_capacity)

            # Validar DESPUÉS de agregar todo
            network.validate_network()
            return network

        except ParseError:
            raise
        except Exception as error:
            raise ParseError(f"Error construyendo Network: {error}")

    def _create_drones(self, network: Network) -> list[Drone]:
        """Crea la lista de drones.

        Todos comienzan en la zona de inicio con estado IDLE

        Parámetros:
            network: Instancia de Network ya construida

        Returns:
            Lista de instancias de Drone
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
    """Función de conveniencia para parsear un archivo .map

    Args:
        filepath: Ruta al archivo .map

    Returns:
        Tupla (Network, lista[drones], num_drones)

    Raises:
        ParseError: Si hay error de sintaxis o semántica
        FileNotFoundError: Si el archivo no existe
    """
    parser = MapParser()
    return parser.parse_file(filepath)
