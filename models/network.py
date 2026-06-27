from typing import Optional
 
from pydantic import BaseModel, Field, field_validator, ConfigDict
 
from .zone import Zone
from .connection import Connection

class Network(BaseModel):
    """Modelo de red para el sistema de enrutamiento de drones.
    Define la clase Network que representa el grafo completo con zonas,
    conexiones y estados de validación

    Atributos:
        start_zone: Zona de inicio de todos los drones
        end_zone: Zona destino de todos los drones
        zones: Diccionario de zonas (nombre -> Zone)
        connections: Diccionario de conexiones ((a,b) -> Connection)
    """
    model_config = ConfigDict(frozen=False, validate_assignment=False)

    start_zone: Zone
    end_zone: Zone
    zones: dict[str, Zone] = Field(default_factory=dict)
    connections: dict[tuple[str, str], Connection] = Field(default_factory=dict)

    @field_validator('start_zone', 'end_zone')
    @classmethod
    def zones_differents(cls, value: Zone, info) -> Zone:
        """Valida que start_zone y end_zone sean diferentes"""
        start = info.data.get('start_zone')
        if (info.field_name == 'end_zone' and value == start):
            raise ValueError("No puede iniciar y terminar en la misma zona")
        return value

    def add_zone(self, zone: Zone) -> None:
        """Agrega una zona a la red

        Args:
            zone: la zona a agregar

        Raises:
            ValueError: Si ya existe una zona con el mismo nombre
        """
        if zone.name in self.zones:
            raise ValueError(f"Ya existe una zona con el nombre {zone.name}")
        self.zones[zone.name] = zone

    def add_connection(
            self, zone_a: Zone, zone_b: Zone, max_capacity: int = 1
    ) -> None:
        """Agrega una conexión bidireccional entre dos zonas.

        Args:
            zone_a: Primera zona
            zone_b: Segunda zona
            max_capacity: Capacidad máxima de la conexión (default=1)

        Raises:
            ValueError si alguna zona no existe o la conexión ya existe
        """
        if zone_a.name not in self.zones:
            raise ValueError(f"'{zone_a.name}' no existe en la red")
        if zone_b.name not in self.zones:
            raise ValueError(f"'{zone_b.name}' no existe en la red")

        # Normalizar clave (orden independiente)
        key = tuple(sorted([zone_a.name, zone_b.name]))


        if key in self.connections:
            raise ValueError(
                f"Ya existe una conexión entre '{zone_a.name}'-'{zone_b.name}'"
            )

        conn = Connection(
            zone_a=zone_a,
            zone_b=zone_b,
            max_capacity=max_capacity
        )

        self.connections[key] = conn

    def get_zone(self, name: str) -> Optional[Zone]:
        """Busca una zona por nombre.

        Args:
            name: Nombre de la zona

        Returns:
            La zona si existe, None en caso contrario
        """
        return self.zones.get(name)

    def get_neighbors(self, zone: Zone) -> list[Zone]:
        """Retorna todas las zonas conectadas directamente a una zona

        Args:
            zone: La zona de referencia

        Return:
            Lista de las zonas vecinas
        """
        neighbors = []

        for (a, b), connection in self.connections.items():
            if connection.zone_a == zone:
                neighbors.append(connection.zone_b)
            elif connection.zone_b == zone:
                neighbors.append(connection.zone_a)
        return neighbors

    def get_connection(
            self, zone_a: Zone, zone_b: Zone
    ) -> Optional[Connection]:
        """Busca la conexión entre dos zonas.

        Args:
            zone_a: primera zona
            zone_b: segunda zona

        Returns:
            La conexión si existe, None en caso contrario
        """
        key = tuple(sorted([zone_a.name, zone_b.name]))
        return self.connections.get(key)

    def is_connected(self, zone_a: Zone, zone_b: Zone) -> bool:
        """Comprueba si dos zonas están conectadas directamente.

        Args:
            zone_a: Primera zona
            zone_b: Segunda zona

        Returns:
            True si hay una conexión directa, False en caso contrario
        """
        return self.get_connection(zone_a, zone_b) is not None

    def get_all_zones(self) -> list[Zone]:
        """ Retorna todas las zonas de la red.

        Returns:
            Lista de todas las zonas
        """
        return list(self.zones.values())
    
    def get_all_connections(self) -> list[Connection]:
        """ Retorna todas las conexiones de la red

        Returns:
            Lista de todas las conexiones
        """
        return list(self.connections.values())

    def get_all_accesible_zones(self) -> list[Zone]:
        """Retorna todas las zonas accesibles (not BLOCKED)

        Returns
            Lista de zonas accesibles
        """
        return [zone for zone in self.get_all_zones() if zone.is_accesible]

    def get_zone_count(self) -> int:
        """Retorna el número total de zonas.

        Returns:
            Cantidad de zonas en la red
        """
        return len(self.zones)

    def get_connection_count(self) -> int:
        """
        Retorna el número total de conexiones 

        Return
            Cantidad de conexiones en la red
        """
        return len(self.connections)

    def validate(self) -> bool:
        """ Valida toda la integridad de la red
        
        Validaciones: 
            1. start_zone y end_zone existen en la red
            2. Ambas zonas son accesibles
            3. No hay conexiones a zonas BLOCKED

        Returns:
            True si la red es válida

        Raises:
            ValueError: si la red no cumple validaciones
        """

        # Validar que start y end existen
        if self.start_zone.name not in self.zones:
            raise ValueError(
                f"{self.start_zone.name} no está en la red de zonas")
        if self.end_zone.name not in self.zones:
            raise ValueError(
                f"{self.end_zone.name} no está en la red de zonas"
            )

        # Validar que start y end son accesibles
        if not self.start_zone.is_accesible():
            raise ValueError(
                f"start_zone no puede estar bloqueada"
            )
        if not self.end_zone.is_accesible():
            raise ValueError(
                f"end_zone no puede estar bloqueada"
            )

        # Validar que no hay conexiones a otras zonas BLOCKED
        for conn in self.get_all_connections():
            if not conn.zone_a.is_accesible() or conn.zone_b.is_accesible():
                raise ValueError(
                    f"Conexión {conn.zone_a.name}-{conn.zone_b.__repr_name__} "
                    "conecta a una zona BLOCKED"
                )

        return True

    def reset_occupancy(self) -> None:
        """ Reinicia la ocupancia de todas las zonas y conexiones a 0

        Útil para preparar la red antes de una nueva simulación
        """
        for zone in self.get_all_zones():
            zone.current_occupancy = 0
        for conn in self.get_all_connections:
            conn.current_occupancy = 0

    def __repr__(self) -> str:
        """Representación legible de la red"""
        return (
            f"Network(zones={self.get_zone_count}), "
            f"connections={self.get_connection_count()}, "
            f"start={self.start_zone.name}, end={self.end_zone.name})"
        )
