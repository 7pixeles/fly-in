from src.network import Network
from src.drone import Drone
from src.zone import Zone, ZoneType
from src.colours import DroneState
from src.exceptions import SimulationError


class Simulator:
    """Engine that runs the turn-by-turn drone simulation.

    Manages drone movement, capacity constraints, conflict
    resolution, and metrics collection across all simulation turns.

    Attributes:
        verbose: Whether to print debug information.
        simulation_turn: List of output strings, one per turn.
        metrics: Computed performance metrics after simulation.
    """

    def __init__(self, verbose: bool = False):
        """Initialize the simulator.

        Args:
            verbose: If True, print debug information during simulation.
        """
        self.verbose = verbose
        self.simulation_turn: list[str] = []
        self.metrics: dict[str, int | float] = {}
        self.reservations: dict[str, dict[int, int]] = {}

    def exe(
        self, network: Network, drones: list[Drone]
    ) -> tuple[list[str], int, dict[str, int | float]]:
        """Execute the full simulation until all drones are delivered.

        Args:
            network: The network graph to simulate on.
            drones: List of drones with planned routes.

        Returns:
            Tuple of (turn outputs, final turn count, metrics dict).

        Raises:
            SimulationError: If a drone has no route, the simulation
                exceeds max turns, or a deadlock is detected.
        """
        for dron in drones:
            if not dron.has_route_planned():
                raise SimulationError(
                    f"Dron {dron.id} no tiene ruta planeada")

        self.simulation_turn = []
        initial_costs = {d.id: d.get_steps_remaining() for d in drones}
        final_turn = 0
        max_turns = 1000
        turns_without_movement = 0
        max_without_movement = 20

        while not self._all_delivered(drones):
            final_turn += 1
            if final_turn > max_turns:
                raise SimulationError(
                    f"Simulation exceeded {max_turns} turns")

            turn_output = self._run_turn(network, drones, final_turn)
            self.simulation_turn.append(turn_output)

            if not turn_output:
                turns_without_movement += 1
                if turns_without_movement >= max_without_movement:
                    raise SimulationError(
                        f"Deadlock: no movement for "
                        f"{max_without_movement} turns")
            else:
                turns_without_movement = 0

        self._clean_occupancy(network)
        self.metrics = self._calc_metrics(
            final_turn, drones, initial_costs)
        return self.simulation_turn, final_turn, self.metrics

    def _all_delivered(self, drones: list[Drone]) -> bool:
        """Check if all drones have reached the end zone.

        Args:
            drones: List of drones to check.

        Returns:
            True if every drone is in DELIVERED state.
        """
        return all(d.state == DroneState.DELIVERED for d in drones)

    def _get_effective_capacity(
        self, zone: Zone, network: Network
    ) -> int:
        """Get effective capacity as min of zone and incoming connections.

        For each zone, the effective capacity is the minimum of its
        own max_drones and the max_link_capacity of all adjacent
        connections. This prevents bottlenecks where a zone has high
        capacity but is fed by low-capacity connections.

        Args:
            zone: The zone to compute capacity for.
            network: The network graph.

        Returns:
            The effective capacity value.
        """
        incoming_caps: list[int] = []
        for conn in network.get_all_connections():
            if conn.zone_a == zone or conn.zone_b == zone:
                incoming_caps.append(conn.max_capacity)
        if not incoming_caps:
            return zone.max_drones
        return min(zone.max_drones, min(incoming_caps))

    def _can_reserve(
        self, zone: Zone, arrival_turn: int, network: Network
    ) -> bool:
        """Check if a zone has capacity for a drone at a given turn.

        Considers both the zone's current occupancy and all future
        reservations at the arrival turn, using effective capacity.

        Args:
            zone: The destination zone.
            arrival_turn: The turn when the drone would arrive.
            network: The network graph.

        Returns:
            True if the zone can accept a drone at that turn.
        """
        if zone.zone_type == ZoneType.BLOCKED:
            return False
        effective = self._get_effective_capacity(zone, network)
        current = zone.current_occupancy
        reserved = self.reservations.get(
            zone.name, {}).get(arrival_turn, 0)
        return (current + reserved) < effective

    def _reserve(self, zone: Zone, arrival_turn: int) -> None:
        """Register a future arrival at a zone.

        Args:
            zone: The zone where a drone will arrive.
            arrival_turn: The turn of the expected arrival.
        """
        if zone.name not in self.reservations:
            self.reservations[zone.name] = {}
        turn_res = self.reservations[zone.name]
        turn_res[arrival_turn] = turn_res.get(arrival_turn, 0) + 1

    def _cancel_reservation(
        self, zone: Zone, arrival_turn: int
    ) -> None:
        """Cancel a reservation when a drone actually arrives.

        Args:
            zone: The zone where the drone arrived.
            arrival_turn: The turn of the arrival.
        """
        if zone.name in self.reservations:
            turn_res = self.reservations[zone.name]
            if arrival_turn in turn_res:
                turn_res[arrival_turn] -= 1
                if turn_res[arrival_turn] <= 0:
                    del turn_res[arrival_turn]

    def _run_turn(
        self, network: Network, drones: list[Drone], turn: int
    ) -> str:
        """Execute a single simulation turn.

        Processes arriving drones first (finishing in-flight transit),
        then attempts to move remaining idle drones. Uses a reservation
        table to prevent drones from entering connections when the
        destination zone will be full upon arrival.

        Args:
            network: The network graph.
            drones: List of all drones.
            turn: The current turn number.

        Returns:
            Space-separated string of movements this turn.
        """
        movements: list[str] = []

        arriving: list[tuple[Drone, Zone]] = []
        arrived_ids: set[int] = set()
        for dron in drones:
            if dron.state == DroneState.DELIVERED:
                continue
            if dron.turns_in_flight > 0:
                dron.turns_in_flight -= 1
                if dron.turns_in_flight == 0:
                    next_zone = dron.get_next_zone()
                    if next_zone is not None:
                        arriving.append((dron, next_zone))

        for dron, next_zone in arriving:
            self._cancel_reservation(next_zone, turn)

            conn = network.get_connection(dron.current_zone, next_zone)
            if conn:
                conn.remove_drone()

            if (dron.current_zone != dron.start_zone
                    and dron.current_zone.zone_type != ZoneType.BLOCKED):
                dron.current_zone.remove_drone()

            dron.advance_position(next_zone)

            if next_zone != network.end_zone:
                next_zone.add_drone()

            dron.state = DroneState.MOVING
            arrived_ids.add(dron.id)
            movements.append(f"D{dron.id}-{next_zone.name}")

            if dron.current_zone == network.end_zone:
                dron.state = DroneState.DELIVERED
                next_zone.remove_drone()

        candidates: list[tuple[Drone, Zone]] = []
        for dron in drones:
            if dron.state == DroneState.DELIVERED:
                continue
            if dron.turns_in_flight > 0:
                continue
            if dron.id in arrived_ids:
                continue

            next_zone = dron.get_next_zone()
            if next_zone is None:
                if dron.current_zone == network.end_zone:
                    dron.state = DroneState.DELIVERED
                continue

            candidates.append((dron, next_zone))

        for dron, next_zone in candidates:
            if dron.state == DroneState.DELIVERED:
                continue
            if not self._can_move(network, dron, next_zone):
                continue

            if next_zone.zone_type == ZoneType.RESTRICTED:
                conn = network.get_connection(
                    dron.current_zone, next_zone)
                if conn is None or not conn.can_fit_drone():
                    continue
                if not self._can_reserve(
                        next_zone, turn + 2, network):
                    continue
                conn.add_drone()
                self._reserve(next_zone, turn + 2)
                dron.turns_in_flight = 1
                dron.state = DroneState.IN_TRANSIT
                movements.append(f"D{dron.id}-{conn.name}")
            else:
                if not self._can_reserve(
                        next_zone, turn + 1, network):
                    continue

                if (dron.current_zone != dron.start_zone
                        and dron.current_zone.zone_type
                        != ZoneType.BLOCKED):
                    dron.current_zone.remove_drone()

                if next_zone != network.end_zone:
                    next_zone.add_drone()

                dron.advance_position(next_zone)
                movements.append(f"D{dron.id}-{next_zone.name}")

                if dron.current_zone == network.end_zone:
                    dron.state = DroneState.DELIVERED
                    next_zone.remove_drone()

        return " ".join(movements)

    def _can_move(
            self, network: Network, dron: Drone, next_zone: Zone) -> bool:
        """Check if a drone can move to the next zone.

        Args:
            network: The network graph.
            dron: The drone attempting to move.
            next_zone: The destination zone.

        Returns:
            True if the move is allowed by capacity and state rules.
        """
        if not next_zone.is_accesible():
            return False

        if next_zone == network.end_zone:
            return True

        if not next_zone.can_fit_drone():
            return False

        if dron.state == DroneState.IN_TRANSIT:
            return False

        return True

    def _clean_occupancy(self, network: Network) -> None:
        """Reset all zone and connection occupancy to zero.

        Args:
            network: The network whose occupancy to clear.
        """
        for zona in network.get_all_zones():
            zona.current_occupancy = 0
        for conn in network.get_all_connections():
            conn.current_occupancy = 0

    def _calc_metrics(
        self,
        final_turn: int,
        drones: list[Drone],
        initial_costs: dict[int, int] | None = None,
    ) -> dict[str, int | float]:
        """Compute performance metrics from the simulation.

        Args:
            final_turn: Total number of turns executed.
            drones: List of all drones.
            initial_costs: Optional dict of drone ID to initial steps.

        Returns:
            Dictionary with metrics including total turns, movements,
            averages, and drone count.
        """
        n_turns = len(self.simulation_turn)
        total_movements = sum(
            len(line.split()) for line in self.simulation_turn
            if line
        )
        avg_moves = (
            total_movements / n_turns if n_turns > 0 else 0
        )

        if initial_costs:
            total_cost = sum(initial_costs.values())
        else:
            total_cost = sum(d.get_steps_remaining() for d in drones)
        avg_steps = total_cost / len(drones) if drones else 0

        return {
            "final_turn": final_turn,
            "total_movements": total_movements,
            "average_moves_turn": round(avg_moves, 2),
            "total_cost": total_cost,
            "average_steps_dron": round(avg_steps, 2),
            "drones_totales": len(drones),
        }

    def get_formatted_exit(self) -> str:
        """Get the simulation output as a multi-line string.

        Returns:
            Newline-joined turn outputs.
        """
        return "\n".join(self.simulation_turn)

    def get_resume(self) -> str:
        """Get a formatted summary of simulation metrics.

        Returns:
            Multi-line string with key performance metrics,
            or a message if no simulation has been run.
        """
        if not self.metrics:
            return "No hay simulacion ejecutada"

        resume = [
            "=== RESUMEN DE SIMULACION ===",
            f"Turnos totales: {self.metrics['final_turn']}",
            f"Drones: {self.metrics['drones_totales']}",
            f"Total de movimientos: {self.metrics['total_movements']}",
            "Promedio de movimientos/turno: "
            f"{self.metrics['average_moves_turn']}",
            f"Costo total de rutas: {self.metrics['total_cost']}",
            "Promedio de pasos/dron: "
            f"{self.metrics['average_steps_dron']}",
        ]
        return "\n".join(resume)
