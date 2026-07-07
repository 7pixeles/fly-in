import random
from copy import deepcopy

from models import Network, Drone, Zone


def _can_enter_zone(zone: Zone, occupancy_zone: dict[str, int],
                    planned_moves: dict[str, list[Drone]]) -> bool:
    """Verifica si un dron puede entrar a una zona

    Considera:
    1. La zona es accesible (no BLOCKED)
    2. La zona tiene capacidad disponible (ocupancy < max_drones)
    3. Los movimientos planeados en el turno respetan la capacidad.

    Parámetros:
        - zone: La zona a evaluar.
        - occupancy_zone: {nombre_zona: cantidad_drones}
        - planned_moves: {nombre_zona: [drones_planeados]}

    Returns:
        - True si el dron puede entrar, False en caso contrario.
    """
    if not zone.is_accesible():
        return False

    current_occupancy = occupancy_zone.get(zone.name, 0)
    entering_drones = len(planned_moves.get(zone.name, []))
    post_move_occupancy = current_occupancy + entering_drones + 1

    if post_move_occupancy > zone.max_drones:
        return False

    return True


def create_initial_assigment(
        route_by_drone: dict[int, list[list[Zone]]]
        ) -> dict[int, list[Zone]]:
    """Crea asignación inicial: cada dron en su primera (mejor) ruta

    Parámetros:
        route_by_drone: {dron_id: [ruta_A, ruta_B, ruta_C]}

    Returns:
        {dron_id: ruta_A}
    """

    assignation = {}

    for dron_id, route in route_by_drone.items():
        if not route:
            raise ValueError(f"Dron {dron_id} no tiene rutas disponibles")
        assignation[dron_id] = route[0]

    return assignation


def ev_assignment(
        assignment: dict[int, list[Zone]],
        network: Network, drones: list[Drone]) -> int:
    """Simula una asignación de rutas y retorna el valor estimado.

    Parámetros:
        - assignment: {drone_id: lista_zonas}
        - network: La red de zonas y conexiones.
        - drones: Una lista de drones disponibles (no se modifica)

    Returns:
        - int: Turno en que el último dron llegó
            (o penalización si hay deadlocks)

    Nota:
        - Crea copias de drones para simular sin afectar originales
        - Respeta capacidades de zona y conexiones
        - Detecta deadlock simple (10+ turnos sin movimiento)
    """

    # Copiar drones para simular sin modificar originales
    simulated_drones = deepcopy(drones)

    # Asignar rutas
    for drone in simulated_drones:
        route = assignment.get(drone.id)

        if route is None:
            raise ValueError(f"No hay ruta asignada para el dron {drone.id}")
        drone.set_route(route)

    # Copiar estado de red (solo ocupancias)
    occupancy_zone: dict[str, int] = {}
    for zone in network.get_all_zones():
        occupancy_zone[zone.name] = 0

    # Inicialmente, todos los drones están en su zona inicial
    initial_zone = network.start_zone
    occupancy_zone[initial_zone.name] = len(simulated_drones)

    turn = 0
    delivered: set[int] = set()
    turns_without_movement = 0
    max_turns = 500

    # Simulación de turnos
    while len(delivered) < len(simulated_drones):
        turn += 1

        if turn > max_turns:
            # Penalización por deadlock
            return max_turns

        # Paso 1: Recolectar intentos de movimiento
        valid_moves: dict[str, list[Drone]] = {}

        for dron in simulated_drones:
            if dron.id in delivered:
                continue

            next_zone = dron.get_next_zone()

            if next_zone is None:
                delivered.add(dron.id)
                continue

            if _can_enter_zone(next_zone, occupancy_zone, valid_moves):
                if next_zone.name not in valid_moves:
                    valid_moves[next_zone.name] = []
                valid_moves[next_zone.name].append(dron)

        # Paso 2: Procesar movimientos válidos
        moved_drones = 0

        for name_zone, dron_to_move in valid_moves.items():
            dest_zone = network.get_zone(name_zone)

            if dest_zone is None:
                raise ValueError(
                    f"La zona '{name_zone}' no existe en la red")

            for dron in dron_to_move:
                # Eliminar de la zona anterior
                prev_zone = dron.current_zone
                occupancy_zone[prev_zone.name] -= 1

                # Avanzar posición
                dron.advance_position(dest_zone)

                # Agregar a nueva zona
                occupancy_zone[name_zone] += 1
                moved_drones += 1

                # Verificar si llegó
                if dron.current_zone == dron.end_zone:
                    delivered.add(dron.id)

        # Paso 3: Detectar deadlocks (+10 turnos sin movimiento)
        if moved_drones == 0:
            turns_without_movement += 1

            if turns_without_movement > 10:
                return max_turns

        else:
            turns_without_movement = 0

    return turn


def select_different_route(
        route: list[list[Zone]],
        current: list[Zone]) -> list[Zone]:
    """Selecciona una ruta diferente de la actual.

    De las 3 rutas disponibles, elige una que NO sea la actual.

    Parámetros:
        route: Lista de rutas disponibles
        current: Ruta que NO queremos

    Return:
        Una ruta diferente (o la misma si no hay alternativa)
    """

    alt = [r for r in route if r != current]

    if not alt:
        return current  # No hay alternativa

    return random.choice(alt)


def calc_probability(it: int, max_it: int) -> float:
    """Calcula probabilidad de aceptar un movimiento peor.

    Usa simulated annealing: probabilidad decrece de 30% a 0%.

    Parámetros:
        it: Iteración actual (1 a iteraciones_max)
        max_it: Total de iteraciones

    Retorna:
        float: Probabilidad entre 0.0 y 1.0
    """
    return 0.30 * (1.0 - (it / max_it))


def copy_assignment(
        assignment: dict[int, list[Zone]]
        ) -> dict[int, list[Zone]]:
    """Copia una asignación de rutas.

    Las rutas (listas de Zone) se copian (referencia),
    no necesitan deep copy porque Zone es inmutable en el contexto
    de este algoritmo.
    """

    return assignment.copy()


def select_random_id(drones: list[Drone]) -> int:
    """Selecciona aleatoriamente el ID de un dron.

    Parámetros:
        drones: Lista de drones

    Retorna:
        int: ID de un dron aleatorio
    """

    if not drones:
        raise ValueError("Lista de drones vacía")

    dron = random.choice(drones)
    return dron.id
