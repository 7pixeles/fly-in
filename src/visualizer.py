import random

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
    "crimson": Color.CRIMSON.value[1],
    "black": Color.BLACK.value[1],
    "brown": Color.BROWN.value[1],
    "maroon": Color.MAROON.value[1],
    "gold": Color.GOLD.value[1],
    "darkred": Color.DARKRED.value[1],
    "violet": Color.VIOLET.value[1],
    "cyan": "\033[36m",
    "lime": "\033[92m",
    "magenta": "\033[95m",
    "gray": "\033[90m",
    "grey": "\033[90m",
}

RAINBOW_COLORS: list[str] = [
    Color.RED.value[1],
    Color.ORANGE.value[1],
    Color.YELLOW.value[1],
    Color.GREEN.value[1],
    Color.BLUE.value[1],
    Color.PURPLE.value[1],
    Color.CRIMSON.value[1],
    Color.VIOLET.value[1],
]

RESET = "\033[0m"


def colorize_rainbow(text: str) -> str:
    return "".join(
        f"{RAINBOW_COLORS[i % len(RAINBOW_COLORS)]}{char}{RESET}"
        for i, char in enumerate(text)
    )


BOLD = "\033[1m"
DIM = "\033[2m"


def get_zone_color(zone: Zone) -> str:
    """Get the ANSI color code for a zone.

    Uses the zone's explicit color if defined, otherwise falls back
    to a default color based on the zone type. If the zone color is
    'rainbow', a random color is selected from the rainbow palette.

    Args:
        zone: The zone to get the color for.

    Returns:
        ANSI escape sequence string for the zone's color.
    """
    if zone.color:
        if zone.color == "rainbow":
            return random.choice(RAINBOW_COLORS)
        if zone.color in COLOR_MAP:
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
    print(f"\n{BOLD}=== NETWORK ==={RESET}")
    for zone in network.get_all_zones():
        if zone.color == "rainbow":
            name_display = f"{colorize_rainbow(zone.name):<15}"
        else:
            color = get_zone_color(zone)
            name_display = f"{color}{zone.name:<15}{RESET}"
        t = zone.zone_type.name
        extra = ""
        if zone.zone_type != ZoneType.BLOCKED:
            extra = f" (capacity:{zone.max_drones})"
        print(f"  {name_display} [{t}]{extra}"
              f" ({zone.x},{zone.y})")

    # print(f"\n{BOLD}=== CONNECTIONS ==={RESET}")
    # for conn in network.get_all_connections():
    #     print(f"  {conn.zone_a.name} <-> {conn.zone_b.name}"
    #           f" (capacity:{conn.max_capacity})")
    print()


def print_drones(drones: list[Drone]) -> None:
    """Print the current state of all drones.

    Args:
        drones: List of drones to display.
    """
    print(f"{BOLD}=== DRONES ==={RESET}")
    for dron in drones:
        print(f"  D{dron.id} in {dron.current_zone.name},"
              f" [{dron.state.value}],"
              f" remaining steps:{dron.get_steps_remaining()}")
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
        print(f"{DIM}Turn {turn_num}: (without movements){RESET}")
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
    print(f"Turn {turn_num}: {' '.join(colored_parts)}")


def print_drone_positions(drones: list[Drone]) -> None:
    """Print the current position of each drone.

    Args:
        drones: List of drones to display.
    """
    for dron in drones:
        if dron.current_zone.color == "rainbow":
            name_display = colorize_rainbow(dron.current_zone.name)
        else:
            c = get_zone_color(dron.current_zone)
            name_display = f"{c}{dron.current_zone.name}{RESET}"
        state = dron.state.value
        print(
            f"  D{dron.id}: {name_display}"
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
    print(f"{BOLD}  SIMULATION - {final_turn} turnos{RESET}")
    print(f"{BOLD}{'=' * 50}{RESET}\n")

    print_network(network)
    print_drones(drones)

    print(f"{BOLD}=== EXECUTION ==={RESET}")
    for i, turn_output in enumerate(simulation_output, start=1):
        print_turn(i, turn_output, drones)
    print()
