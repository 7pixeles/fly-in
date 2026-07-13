from src.zone import Zone, ZoneType
from src.network import Network
from src.colours import Color
from src.drone import Drone


COLOR_MAP: dict[str, str] = {
    "green": Color.GREEN.value[1],
    "red": Color.RED.value[1],
    "blue": Color.BLUE.value[1],
    "yellow": Color.YELLOW.value[1],
    "purple": Color.PURPLE.value[1],
    "orange": Color.ORANGE.value[1],
    "gray": "\033[90m",
    "grey": "\033[90m",
}

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def get_zone_color(zone: Zone) -> str:
    """Get the ANSI color code for a zone.

    Uses the zone's explicit color if defined, otherwise falls back
    to a default color based on the zone type.

    Args:
        zone: The zone to get the color for.

    Returns:
        ANSI escape sequence string for the zone's color.
    """
    if zone.color and zone.color in COLOR_MAP:
        return COLOR_MAP[zone.color]
    type_colors = {
        ZoneType.NORMAL: Color.BLUE.value[1],
        ZoneType.RESTRICTED: Color.RED.value[1],
        ZoneType.PRIORITY: Color.GREEN.value[1],
        ZoneType.BLOCKED: "\033[90m",
    }
    return type_colors.get(zone.zone_type, RESET)


def print_network(network: Network) -> None:
    """Print the network topology with colored zone and connection info.

    Args:
        network: The network to display.
    """
    print(f"\n{BOLD}=== RED DE ZONAS ==={RESET}")
    for zone in network.get_all_zones():
        c = get_zone_color(zone)
        t = zone.zone_type.name
        extra = ""
        if zone.zone_type != ZoneType.BLOCKED:
            extra = f" (cap:{zone.max_drones})"
        print(f"  {c}{zone.name}{RESET} [{t}]{extra}"
              f" ({zone.x},{zone.y})")

    print(f"\n{BOLD}=== CONEXIONES ==={RESET}")
    for conn in network.get_all_connections():
        print(f"  {conn.zone_a.name} <-> {conn.zone_b.name}"
              f" (cap:{conn.max_capacity})")
    print()


def print_drones(drones: list[Drone]) -> None:
    """Print the current state of all drones.

    Args:
        drones: List of drones to display.
    """
    print(f"{BOLD}=== DRONES ==={RESET}")
    for dron in drones:
        print(f"  D{dron.id} en {dron.current_zone.name}"
              f" [{dron.state.value}]"
              f" pasos_rest:{dron.get_steps_remaining()}")
    print()


def print_turn(
    turn_num: int, output: str, drones: list[Drone]
) -> None:
    """Print a single turn's movements with colors.

    Args:
        turn_num: The turn number.
        output: Space-separated movements string.
        drones: List of drones (for context).
    """
    if not output:
        print(f"{DIM}Turno {turn_num}: (sin movimientos){RESET}")
        return

    parts = output.split(" ")
    colored_parts: list[str] = []
    for part in parts:
        if part.startswith("D"):
            dash_idx = part.index("-")
            drone_id = part[:dash_idx]
            target = part[dash_idx + 1:]
            colored_parts.append(
                f"{Color.YELLOW.value[1]}{drone_id}{RESET}"
                f"-{Color.GREEN.value[1]}{target}{RESET}")
    print(f"Turno {turn_num}: {' '.join(colored_parts)}")


def print_drone_positions(drones: list[Drone]) -> None:
    """Print the current position of each drone.

    Args:
        drones: List of drones to display.
    """
    for dron in drones:
        c = get_zone_color(dron.current_zone)
        state = dron.state.value
        print(
            f"  D{dron.id}: {c}{dron.current_zone.name}{RESET}"
            f" [{state}]"
        )


def visualize_simulation(
    network: Network,
    drones: list[Drone],
    simulation_output: list[str],
    final_turn: int,
) -> None:
    """Run the full visual representation of the simulation.

    Displays the network topology, drone states, and step-by-step
    turn execution with colored terminal output.

    Args:
        network: The network graph.
        drones: List of drones after simulation.
        simulation_output: List of turn output strings.
        final_turn: Total number of turns executed.
    """
    print(f"\n{BOLD}{'=' * 50}{RESET}")
    print(f"{BOLD}  SIMULACION - {final_turn} turnos{RESET}")
    print(f"{BOLD}{'=' * 50}{RESET}\n")

    print_network(network)
    print_drones(drones)

    print(f"{BOLD}=== EJECUCION ==={RESET}")
    for i, turn_output in enumerate(simulation_output, start=1):
        print_turn(i, turn_output, drones)
    print()
