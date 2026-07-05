from models import Network, Drone, Zone
from utils.enums import DroneState
from utils.exceptions import SimulationError

class Simulator:
    """Motor de simulación de rutas de drones.
    
    Ejecuta turno a turno el movimiento de drones siguiendo sus rutas
    planeadas, respetando todas las restricciones de capacidad y movimiento.
    """
    def __init__(self, verbose: bool = False):
        """Inicializa el simulador.
        
        Parámetros:
            verbose: Imprimir información de depuración (default: False)
        """
        self.verbose = verbose
        self.network = None
        self.drones = None
        self.simulation_turn = []
        self.metrics = {}
    
    def exe(self, network: Network, drones: list[Drone]) -> tuple[list[str], int, dict]:
        """Ejecuta la simulación completa.
        
        Parámetros:
            network: Red de zonas y conexiones
            drones: Lista de drones con rutas planeadas
        
        Return:
            (lineas_salida, final_turn, metrics)
        
        Raise:
            SimulationError: Si hay error en la simulación
        """
        
        self.network = network
        self.drones = drones
        self.simulation_turn = []
        
        # Validar entrada
        for dron in self.drones:
            if not dron.has_route_planned():
                raise SimulationError(f"Dron {dron.id} no tiene ruta planeada")
        
        # Inicializar estado
        turn = 0
        delivered = set()  # IDs de drones que llegaron
        max_turn = 1000  # Seguridad
        
        # Ocupancia inicial: todos los drones en start_zone
        start = self.network.start_zone
        for dron in self.drones:
            start.add_drone()

        if self.verbose:
            print(f"Simulación iniciada: {len(self.drones)} drones")
            print(f"Zona inicio: {start.name}, Zona fin: {self.network.end_zone.name}")

        # Simulación turno a turno
        while len(delivered) < len(self.drones):
            turn += 1
            
            if turn > max_turn:
                raise SimulationError(
                    f"Simulación excedió {max_turn} "
                    "turnos (deadlock probable)")

            # PASO 1: Recolectar movimientos válidos
            movements_this_turn = []

            for dron in self.drones:
                if dron.id in delivered:
                    continue
                
                next_zone = dron.get_next_zone()
                
                if next_zone is None:
                    # Dron llegó pero no fue marcado como entregado
                    raise SimulationError(
                        f"Dron {dron.id} sin siguiente zona pero no entregado")
                
                if self._can_move(dron, next_zone):
                    movements_this_turn.append((dron, next_zone))
            
            # PASO 2: Ejecutar movimientos
            if movements_this_turn:
                for dron, next_zone in movements_this_turn:
                    dron.current_zone.remove_drone()
                    dron.advance_position(next_zone)
                    next_zone.add_drone()
                    if dron.current_zone == self.network.end_zone:
                        delivered.add(dron.id)
                
                # PASO 3: Guardar línea de salida
                line = " ".join([f"D{dron.id}-{next_zone.name}" 
                                 for dron, next_zone in movements_this_turn])
                self.simulation_turn.append(line)
                
                if self.verbose:
                    print(f"Turno {turn}: {line}")
            else:
                if len(delivered) < len(self.drones):
                    raise SimulationError(f"Deadlock en turno {turn}: {len(self.drones) - len(delivered)} drones bloqueados")
        
        # Limpiar ocupancias (devolver drones a 0)
        self._clean_occupancy()
        
        # Calcular métricas
        self.metrics = self._calc_metrics(turn)
        
        if self.verbose:
            print(f"\nSimulación completada en {turn} turnos")
            print(f"Métricas: {self.metrics}")
        
        return self.simulation_turn, turn, self.metrics
    
    def _can_move(self, dron: Drone, next_zone: Zone) -> bool:
        """Verifica si un dron puede moverse a la siguiente zona.
        
        Valida:
        1. La zona es accesible (no BLOCKED)
        2. La zona tiene capacidad disponible
        3. El dron no está en tránsito (en vuelo)
        
        Parámetros:
            dron: Dron que intenta moverse
            next_zone: Zona destino
        
        Retorna:
            bool: True si puede moverse
        """

        if not next_zone.is_accesible():
            return False

        if next_zone == self.network.end_zone:
            return next_zone.can_fit_drone()

        if not next_zone.can_fit_drone():
            return False

        if dron.state == DroneState.IN_TRANSIT:
            return False
    
        return True
    
    def _clean_occupancy(self) -> None:
        """Reinicia las ocupancias de zonas a 0.
        
        Necesario después de la simulación para que los modelos
        queden en estado limpio.
        """
        for zona in self.network.get_all_zones():
            zona.current_occupancy = 0
    
    def _calc_metrics(self, final_turn: int) -> dict:
        """Calcula métricas de la simulación.
        
        Parámetros:
            final_turn: Número total de turnos
        
        Retorna:
            Diccionario con métricas
        """
        
        n_turns_movements = len(self.simulation_turn)
        total_movements = sum(
            len(line.split()) for line in self.simulation_turn
        )
        average_moves_turn = (
            total_movements / n_turns_movements 
            if n_turns_movements > 0 
            else 0
        )
        
        # Calcular costo total (suma de pasos por dron)
        total_cost = 0
        for dron in self.drones:
            total_cost += dron.get_steps_remaining()  # Pasos planeados
        
        average_steps_dron = total_cost / len(self.drones) if self.drones else 0
        
        return {
            "final_turn": final_turn,
            "total_movements": total_movements,
            "average_moves_turn": round(average_moves_turn, 2),
            "total_cost": total_cost,
            "average_steps_dron": round(average_steps_dron, 2),
            "drones_totales": len(self.drones),
        }
    
    def get_formatted_exit(self) -> str:
        """Retorna la salida de simulación como string formateado.
        
        Retorna:
            String con cada turno en una línea
        """
        return "\n".join(self.simulation_turn)
    
    def get_resume(self) -> str:
        """Retorna un resumen de la simulación.
        
        Retorna:
            String con información de métricas
        """
        
        if not self.metrics:
            return "No hay simulación ejecutada"
        
        resume = []
        resume.append("=== RESUMEN DE SIMULACIÓN ===")
        resume.append(
            f"Turnos totales: {self.metrics['final_turn']}")
        resume.append(
            f"Drones: {self.metrics['drones_totales']}")
        resume.append(
            f"Total de movimientos: {self.metrics['total_movements']}")
        resume.append(
            "Promedio de movimientos/turno: "
            f"{self.metrics['average_moves_turn']}")
        resume.append(
            f"Costo total de rutas: {self.metrics['total_cost']}")
        resume.append(
            f"Promedio de pasos/dron: {self.metrics['average_steps_dron']}")
        
        return "\n".join(resume)