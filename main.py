import sys
from pathlib import Path

from parser import parse_map, MapParser
from utils.exceptions import ParseError, PathfindingError, SimulationError
from algorithms.pathfinding import find_routes_multidrone
from simulation import Simulator


def main(map_path: str) -> int:
    """ Ejecuta flujo completo. 
    
    Parámetros: 
        map_path: ruta al archivo .map
        
    Return: 
        int: código de salida (0 Éxito, 1 Error)"""
    

    try:
        # Validar que el archivo existe
        path = Path(map_path)
        if not path.exists:
            print(f"Error: Archivo {map_path} no encontrado", file=sys.stderr)
            return 1
        

        print(f"Cargando mapa: {map_path}")
        print()

        print("=== FASE 1: PARSING ===")
        try:
            network, drones, nb_drones = parse_map(str(map_path))
        except ParseError as error:
            print(f"Error al parsear {error}", file=sys.stderr)
            return 1
        
        print(f"✓ Mapa cargado exitosamente")
        print(f"  • Drones: {nb_drones}")
        print(f"  • Zonas: {network.get_zone_count()}")
        print(f"  • Conexiones: {network.get_connection_count()}")
        print(f"  • Inicio: {network.start_zone.name}")
        print(f"  • Destino: {network.end_zone.name}")
        print()

        print("=== FASE 2: PATHFINDING ===")
        try:
            drones_with_routes, estimated_turn = find_routes_multidrone(
                network,
                drones,
                max_iterations=500,
                verbose=False
            )
        except PathfindingError as error:
            print(f"Error en pathfinding: {error}", file=sys.stderr)
            return 1
        
        print(f"✓ Rutas calculadas")
        print(f"  • Turnos estimados: {estimated_turn}")
        print(f"  • Rutas asignadas:")
        for drones in drones_with_routes:
            route_str = " → ".join([z.name for z in drones.planned_route])
            steps = drones.get_steps_remaining()
            print(f"    - D{drones.id}: {route_str} ({steps} pasos)")
        print()

        print("=== FASE 3: SIMULACIÓN ===")
        try:
            simulator = Simulator(verbose=False)
            lines_start, final_turn, metrics = simulator.exe(
                network,
                drones_with_routes
            )
        except SimulationError as error:
            print(f"Error en simulación: {error}", file=sys.stderr)
            return 1
        
        print(f"✓ Simulación completada")
        print()

        print("=== SALIDA DE SIMULACIÓN ===")
        exit = simulator.get_formatted_exit()
        print(exit)
        print()

        print(simulator.get_resume())
        print()

        print("=== VALIDACIÓN ===")
        if final_turn > 0:
            print(f"✓ Simulación válida: {final_turn} turno(s)")
        else:
            print("✗ Simulación inválida: 0 turnos", file=sys.stderr)
            return 1
        
        if len(lines_start) == final_turn:
            print(f"✓ Salida consistente: {len(lines_start)} líneas de output")
        else:
            print(f"⚠ Inconsistencia: {len(lines_start)} "
                  f"líneas pero {final_turn} turnos")
        
        print()
        return 0

    except ParseError as e:
        print(f"Error de parsing: {e}", file=sys.stderr)
        return 1
    
    except PathfindingError as e:
        print(f"Error de pathfinding: {e}", file=sys.stderr)
        return 1
    
    except SimulationError as e:
        print(f"Error de simulación: {e}", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"Error inesperado: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def print_instructions() -> None:
    """Imprime instrucciones de uso."""
    print("Uso: python main.py <archivo_mapa>")
    print()
    print("Ejemplo:")
    print("  python main.py maps/example_complex.map")
    print()
    print("Archivos de ejemplo disponibles:")
    print("  • maps/example_simple_fixed.map - Mapa simple (2 drones)")
    print("  • maps/example_complex.map - Mapa complejo")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_instructions()
        sys.exit(1)
    
    map_path = sys.argv[1]
    
    exit_code = main(map_path)
    sys.exit(exit_code)
