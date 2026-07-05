
import random
from copy import deepcopy
 
from models import Network, Drone
 
from .dijkstra import dijkstra, block_route
from utils.exceptions import DijkstraError, PathfindingError
from .utils import (
    ev_assignment,
    create_initial_assigment,
    select_different_route,
    calc_probability,
    copy_assignment,
    select_random_id,
)

class Pathfinder:
    """Clase base abstracta para algoritmos de pathfinding."""
    
    def find_routes(
            self,
            network: Network,
            drones: list[Drone]) -> tuple[list[Drone], int]:
        """Encuentra rutas para todos los drones.
        
        Parámetros:
            network: Red de zonas
            drones: Lista de drones sin rutas
        
        Return:
            (drones_con_rutas, turno_final_estimado)
        
        Debe ser implementado por subclases.
        """
        raise NotImplementedError



class HeuristicPathfinder(Pathfinder):
    """Algoritmo heurístico de pathfinding multi-dron.
    Usa búsqueda local iterativa con simulated annealing.
    """

    def __init__(
            self,
            max_iterations: int = 500,
            max_no_improve: int = 100,
            initial_probability: float = 0.3,
            verbose: bool = False
            ):
        """
        Inicializa el pathfinder heurístico.

        Parámetros:
            max_iterations: iteraciones máximas de búsqueda local
            max_no_improve: iteraciones sin mejora antes de parar
            inicial_probability: Prob. inicial aceptar movimiento peor
            verbose: Imprimir progreso
        """

        self.max_iterations = max_iterations
        self.max_no_improve = max_no_improve
        self.initial_probability = initial_probability
        self.verbose = verbose

        # Estado durante la ejecución
        self.network = None
        self.drones = None
        self.routes_per_dron = None

    def find_routes(self,
                    network: Network,
                    drones: list[Drone]) -> tuple[list[Drone], int]:
        """ Encuentra rutas para todos los drones.
        Ejecuta las fases: Exploración → búsqueda → refinamiento.

        Parámetros:
            network: red de zonas
            drones: Lista de drones sin rutas

        Returns:
            (drones_con_rutas, turno_final_estimado)

        Raise:
            PathfindingError Si no existe solución
        """
        self.network = network
        self.drones = deepcopy(drones)

        try:
            # FASE 1: Exploración
            if self.verbose:
                print("Fase 1: Explorando rutas alternativas...")
            self.routes_per_dron = self._explore_routes()

            # FASE 2: Búsqueda local
            if self.verbose:
                print("Fase 2: Búsqueda local "
                      f"({self.max_iterations} iteraciones)...")
            best_asignment, best_turn = self._local_search()

            # FASE 3: Refinamientos
            if self.verbose:
                print("Fase 3: Refinando solución...")
            final_turn = self._manage_conflict(best_asignment)

            # Asignar rutas a drones
            for dron in self.drones:
                route = best_asignment[dron.id]
                dron.set_route(route)
            
            if self.verbose:
                print(f"Pathfinding completado: {final_turn} turnos estimados")
            
            return self.drones, final_turn

        except Exception as error:
            raise PathfindingError(f"Error en pathfinding: {error}")
    
    def _explore_routes(self) -> dict[int, list[list]]:
        """ Fase 1: Genera 3 rutas alternativas por dron.
        Retorna: {dron_id: [ruta_A], ruta_b, ruta_C}
        
        Raise:
            PathfindingError: Si no existe un camino para el dron
        """

        dron_routes = {}

        for dron in self.drones:
            alt_route = []
            block_zone = set()

            for i in range(3):
                try:
                    route = dijkstra(
                        self.network,
                        dron.start_zone,
                        dron.end_zone,
                        block_zone
                    )
                    alt_route.append(route)
                    block_route(block_zone, route)

                except DijkstraError:
                    # No hay más rutas disponibles
                    if alt_route:
                        # Rellenar con la última encontrada:
                        alt_route.append(alt_route[-1])
                    break
            
            if not alt_route:
                raise PathfindingError(
                    f"No existe un camino para dron {dron.id} "
                    f"desde {dron.start_zone.name} a {dron.end_zone.name}"
                )
            
            dron_routes[dron.id] = alt_route

            if self.verbose:
                print(f"  Dron {dron.id}: {len(alt_route)} ruta(s)")

        return dron_routes
    
    def _local_search(self) -> tuple[dict[int, list], int]:
        """ Fase 2: Búsqueda local iterativa
        Realiza -100 - 500 iteraciones de hill climbing con aceptacion
        probabilística (simulated annealing)

        Return: (mejor_asignación, mejor turno)
        """

        # Asignación inicial: Todos en su mejor ruta
        current_assignment = create_initial_assigment(self.routes_per_dron)

        best_assignment = copy_assignment(current_assignment)
        best_turn = ev_assignment(best_assignment, self.network, self.drones)

        if self.verbose:
            print(f".  Asignación inicial: {best_turn} turnos")
        
        iteration = 0
        no_improve = 0

        # Búsqueda local
        while iteration < self.max_iterations:
            iteration += 1
            no_improve += 1

            # Paso 1: Seleccionar dron aletatorio
            dron_id = select_random_id(self.drones)
    
            # Paso 2: Seleccionar ruta alternativa
            available_routes = self.routes_per_dron[dron_id]
            current_route = current_assignment[dron_id]
            new_route = select_different_route(available_routes, current_route)

            if new_route == current_route:
                continue
        
            # Paso 3: Crear asignación temporal
            temp_assignment = copy_assignment(current_assignment)
            temp_assignment[dron_id] = new_route

            # Paso 4: Evaluar
            temp_turn = ev_assignment(temp_assignment, self.network, self.drones)

            # Paso 5: Aceptar o rechazar
            if temp_turn < best_turn:
                best_assignment = copy_assignment(temp_assignment)
                best_turn = temp_turn
                current_assignment = copy_assignment(temp_assignment)
                no_improve = 0
                
                if self.verbose and iteration % 50 == 0:
                    print(f".  Iteración {iteration}: {best_turn} turnos")

            else:
                # No hay mejora: Aceptar con probabilidad baja
                probability = calc_probability(iteration, self.max_iterations)

                if random.random() < probability:
                    current_assignment = copy_assignment(temp_assignment)


            # Paso 6: Criterio de parada
            if no_improve >= self.max_no_improve:
                if self.verbose:
                    print(f".  Parada anticipada en iteración {iteration}")
                break

        if self.verbose:
            print(f"   Mejor ruta encontrada: {best_turn} turnos")

        return best_assignment, best_turn
    
    def _manage_conflict(self, assignment: dict[int, list]) -> int:
        """Fase 3: Refinamiento y simylación final.
        Realiza una última simulación completa de la mejor asignación.
        
        Se podrían resolver aquí deadlocks de manera automática
        
        Parámetros:
            assignment: Mejor asignación encontrada
            
        Retorna:
            int: Turno final estimado
        """

        return (ev_assignment(assignment, self.network, self.drones))


def find_routes_multidrone(
        network: Network,
        drones: list[Drone],
        pathfinder_class: type = HeuristicPathfinder,
        **kwargs
    ) -> tuple[list[Drone], int]:
    """ Función de conveniencia para encontrar rutas.
    
    Parámetros:
        network: Red de zonas
        drones: lista de drones sin ruta
        pathfinder_class: Clase a instanciar
        **kwargs; Argumentos para el constructor del pathfinder
        
    Retorna:
        (drones_con_rutas, turno_final_estimado)
        
    Ejemplo: 
        drones, turno = find_routes_multidrone(network, drones, verbose=True)
    """
    pathfinder = pathfinder_class(**kwargs)
    return pathfinder.find_routes(network, drones)