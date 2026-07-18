import argparse
import sys
from typing import Any
from pathlib import Path

from src.parser import parse_map
from src.dijkstra import dijkstra
from src.simulation import Simulator
from src.visualizer import visualize_simulation
from src.network import Network
from src.drone import Drone
from src.colours import DroneState
from src.exceptions import ParseError, DijkstraError, SimulationError


def find_routes_multidrone(
    network: Network,
    drones: list[Drone],
    verbose: bool = False,
) -> list["Drone"]:
    """Assign routes to all drones using multi-drone Dijkstra.

    Processes drones sequentially, passing a usage dict to penalize
    zones already chosen by earlier drones. This distributes drones
    across multiple paths to reduce congestion.

    Args:
        network: The network graph to search.
        drones: List of drones needing routes.
        verbose: If True, print warnings for drones with no route.

    Returns:
        The same list of drones with routes assigned.
    """
    usage: dict[str, int] = {}

    for dron in drones:
        route: list[Any] = []
        try:
            route = dijkstra(
                network,
                dron.current_zone,
                dron.end_zone,
                usage=usage,
            )
        except DijkstraError:
            try:
                route = dijkstra(
                    network,
                    dron.current_zone,
                    dron.end_zone,
                )
            except DijkstraError as e:
                if verbose:
                    print("Warning: No route found"
                          f"for D{dron.id}: {e}", file=sys.stderr)
                dron.planned_route = []
                continue

        dron.set_route(route)
        dron.state = DroneState.IDLE
        for zone in route[1:-1]:
            usage[zone.name] = usage.get(zone.name, 0) + 1

    return drones


def main(map_path: str) -> int:
    """Run the full drone simulation pipeline.

    Parses the map, computes paths with multi-drone Dijkstra,
    runs the simulation, and displays results with visualization.

    Args:
        map_path: Path to the map file to process.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    try:
        path = Path(map_path)
        if not path.exists():
            print(
                f"Error: File {map_path} not found",
                file=sys.stderr)
            return 1

        print(f"Loading map: {map_path}\n")

        print("=== PHASE 1: PARSING ===")
        try:
            network, drones, nb_drones = parse_map(str(map_path))
        except ParseError as error:
            print(f"Error parsing: {error}", file=sys.stderr)
            return 1

        print("Map loaded successfully")
        print(f" Drones: {nb_drones}")
        print(f" Zones: {network.get_zone_count()}")
        print(f" Connections: {network.get_connection_count()}")
        print(f" Start: {network.start_zone.name}")
        print(f" Destination: {network.end_zone.name}\n")

        print("=== PHASE 2: PATHFINDING ===")
        try:
            drones = find_routes_multidrone(
                network, drones, verbose=True)
        except DijkstraError as error:
            print(
                f"Pathfinding error: {error}", file=sys.stderr)
            return 1

        for dron in drones:
            if dron.has_route_planned():
                route_str = " -> ".join(
                    [z.name for z in dron.planned_route])
                steps = dron.get_steps_remaining()
                print(f"  D{dron.id}: {route_str} ({steps} steps)")
            else:
                print(f"  D{dron.id}: without route")
        print()

        print("=== PHASE 3: SIMULATION ===")
        try:
            simulator = Simulator(verbose=False)
            lines, final_turn, metrics = simulator.exe(
                network, drones)
        except SimulationError as error:
            print(
                f"Error in Simulation: {error}", file=sys.stderr)
            return 1

        print("Simulation completed\n")

        print("=== SIMULATION OUTPUT ===")
        print(simulator.get_formatted_exit())
        print()

        print(simulator.get_resume())
        print()

        if final_turn > 0:
            print(f"Valid simulation: {final_turn} turn(s)")
        else:
            print(
                "Invalid simulation: 0 turns",
                file=sys.stderr)
            return 1

        print()
        visualize_simulation(
            network, drones, lines, final_turn)

        return 0

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fly-in: Drone simulation pathfinder")
    parser.add_argument("map_path", help="Path to the map file")
    args = parser.parse_args()
    sys.exit(main(args.map_path))
