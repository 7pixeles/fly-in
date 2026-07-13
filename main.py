import argparse
import sys
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
        route: list = []
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
                    print(
                        f"Advertencia: No se encontro ruta "
                        f"para D{dron.id}: {e}", file=sys.stderr)
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
                f"Error: Archivo {map_path} no encontrado",
                file=sys.stderr)
            return 1

        print(f"Cargando mapa: {map_path}\n")

        print("=== FASE 1: PARSING ===")
        try:
            network, drones, nb_drones = parse_map(str(map_path))
        except ParseError as error:
            print(f"Error al parsear: {error}", file=sys.stderr)
            return 1

        print("Mapa cargado exitosamente")
        print(f"  Drones: {nb_drones}")
        print(f"  Zonas: {network.get_zone_count()}")
        print(f"  Conexiones: {network.get_connection_count()}")
        print(f"  Inicio: {network.start_zone.name}")
        print(f"  Destino: {network.end_zone.name}\n")

        print("=== FASE 2: PATHFINDING ===")
        try:
            drones = find_routes_multidrone(
                network, drones, verbose=True)
        except DijkstraError as error:
            print(
                f"Error en pathfinding: {error}", file=sys.stderr)
            return 1

        for dron in drones:
            if dron.has_route_planned():
                route_str = " -> ".join(
                    [z.name for z in dron.planned_route])
                steps = dron.get_steps_remaining()
                print(f"  D{dron.id}: {route_str} ({steps} pasos)")
            else:
                print(f"  D{dron.id}: sin ruta")
        print()

        print("=== FASE 3: SIMULACION ===")
        try:
            simulator = Simulator(verbose=False)
            lines, final_turn, metrics = simulator.exe(
                network, drones)
        except SimulationError as error:
            print(
                f"Error en simulacion: {error}", file=sys.stderr)
            return 1

        print("Simulacion completada\n")

        print("=== SALIDA DE SIMULACION ===")
        print(simulator.get_formatted_exit())
        print()

        print(simulator.get_resume())
        print()

        if final_turn > 0:
            print(f"Simulacion valida: {final_turn} turno(s)")
        else:
            print(
                "Simulacion invalida: 0 turnos",
                file=sys.stderr)
            return 1

        print()
        visualize_simulation(
            network, drones, lines, final_turn)

        return 0

    except Exception as e:
        print(f"Error inesperado: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fly-in: Drone simulation pathfinder")
    parser.add_argument("map_path", help="Path to the map file")
    args = parser.parse_args()
    sys.exit(main(args.map_path))
