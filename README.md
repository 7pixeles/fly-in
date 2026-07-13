*This project has been created as part of the 42 curriculum by ayucarre.*

# Fly-in

Drone routing simulation that navigates multiple drones through a network of connected zones while minimizing total simulation turns and respecting movement constraints.

## Description

Fly-in simulates a fleet of autonomous drones that must travel from a start zone to an end zone across a graph of interconnected zones. The system must handle:

- **Zone types** with different movement costs: normal (1 turn), restricted (2 turns), priority (1 turn, preferred in pathfinding), and blocked (inaccessible).
- **Capacity constraints** on both zones (`max_drones`) and connections (`max_link_capacity`), limiting how many drones can occupy or traverse them simultaneously.
- **Simultaneous movement** with conflict resolution to prevent drones from colliding or exceeding capacity.
- **Turn-based simulation** where the goal is to deliver all drones in the fewest turns possible.

The project is fully object-oriented, type-safe (mypy), and follows flake8 standards.

## Instructions

### Prerequisites

- Python 3.10 or later
- pip

### Setup

```bash
make install
```

This creates a virtual environment and installs dependencies.

### Running

```bash
make run MAP=maps/easy/01_linear_path.txt
```

Or directly:

```bash
PYTHONPATH=. .venv/bin/python main.py maps/easy/01_linear_path.txt
```

### Map Files

Maps are provided under `maps/` in three difficulty levels:

- `maps/easy/` - Simple topologies (2-4 drones)
- `maps/medium/` - Moderate complexity (5-6 drones)
- `maps/hard/` - Complex mazes (8-15 drones)
- `maps/challenger/` - The Impossible Dream (25 drones)

### Available Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies and create venv |
| `make run MAP=<file>` | Run the simulation |
| `make debug MAP=<file>` | Run with pdb debugger |
| `make lint` | Run flake8 and mypy checks |
| `make lint-strict` | Run strict type checking |
| `make clean` | Remove caches and temp files |

## Algorithm

### Pathfinding: Multi-Drone Dijkstra

The pathfinding uses Dijkstra's shortest path algorithm with a **usage-based penalty system** to distribute drones across multiple paths:

1. **Cost function**: Each edge weight = `connection_cost(1) + zone_movement_cost + usage_penalty`.
2. **Usage penalty**: `usage[zone] * 0.5` penalizes zones already selected by earlier drones, encouraging path diversification.
3. **Sequential assignment**: Drones are processed one at a time. After each drone gets its route, the intermediate zones it uses are added to the usage dict.

**Complexity**: O(V^2) per drone where V is the number of zones, due to the simple linear scan implementation. For the graph sizes in this project (up to ~30 nodes), this is negligible.

### Simulation Engine

The simulation runs turn-by-turn with two phases per turn:

1. **Arrival phase**: Drones finishing in-flight transit (from restricted zones) arrive at their destination. Capacity is freed on departure zones and connections.
2. **Departure phase**: Idle drones attempt to move to their next zone, respecting both zone and connection capacity constraints.

Key design decisions:
- Drones moving out of a zone free up capacity for that same turn (arrivals process first).
- Restricted zone movement occupies the connection for 2 turns (drone cannot wait on the connection).
- The end zone has unlimited capacity (all delivered drones are removed from tracking).

### Performance Results

| Map | Drones | Target | Result |
|-----|--------|--------|--------|
| Easy: Linear path | 2 | <= 6 turns | 4 turns |
| Easy: Simple fork | 4 | <= 8 turns | - |
| Easy: Basic capacity | 4 | <= 6 turns | - |
| Medium: Dead end trap | 5 | <= 12 turns | 8 turns |
| Hard: Maze nightmare | 8 | <= 30 turns | 12 turns |

## Visual Representation

The simulation provides colored terminal output to enhance understanding:

- **Network topology**: Zones displayed with colors based on their type (blue=normal, red=restricted, green=priority, gray=blocked) or custom `color` metadata.
- **Turn execution**: Each turn shows drone movements with drone IDs in yellow and destination zones in connections in green.
- **ANSI color codes**: Uses standard terminal escape sequences for cross-platform compatibility.

Example output:

```
Turno 1: D1-waypoint1
Turno 2: D1-waypoint2 D2-waypoint1
Turno 3: D1-goal D2-waypoint2
Turno 4: D2-goal
```

## Project Structure

```
fly-in/
  main.py           # Entry point and pipeline orchestration
  parser.py         # Map file parser with validation
  dijkstra.py       # Pathfinding algorithm
  simulation.py     # Turn-by-turn simulation engine
  visualizer.py     # Colored terminal output
  network.py        # Graph data structure (zones + connections)
  zone.py           # Zone model with occupancy rules
  connection.py     # Connection model with capacity
  drone.py          # Drone model with route tracking
  colours.py        # Color definitions and drone states
  exceptions.py     # Custom exception hierarchy
  maps/             # Test maps organized by difficulty
```

## Map Format

```
nb_drones: 5
start_hub: start 0 0 [color=green]
end_hub: goal 10 10 [color=red]
hub: zone1 3 4 [zone=restricted color=orange]
hub: zone2 6 2 [zone=normal max_drones=2]
connection: start-zone1
connection: zone1-zone2 [max_link_capacity=2]
connection: zone2-goal
```

Supported metadata:
- `zone=<type>`: normal, restricted, priority, blocked
- `color=<name>`: Any single word for terminal coloring
- `max_drones=<n>`: Zone capacity (default: 1)
- `max_link_capacity=<n>`: Connection capacity (default: 1)

## Example

### Input

Using `maps/easy/01_linear_path.txt`:

```
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

This defines 2 drones traveling through a straight line: `start -> waypoint1 -> waypoint2 -> goal`. All zones have capacity 1 except start and goal (capacity 2).

### Output

```
Cargando mapa: maps/easy/01_linear_path.txt

=== FASE 1: PARSING ===
Mapa cargado exitosamente
  Drones: 2
  Zonas: 4
  Conexiones: 3
  Inicio: start
  Destino: goal

=== FASE 2: PATHFINDING ===
  D1: start -> waypoint1 -> waypoint2 -> goal (3 pasos)
  D2: start -> waypoint1 -> waypoint2 -> goal (3 pasos)

=== FASE 3: SIMULACION ===
Simulacion completada

=== SALIDA DE SIMULACION ===
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal

=== RESUMEN DE SIMULACION ===
Turnos totales: 4
Drones: 2
Total de movimientos: 6
Promedio de movimientos/turno: 1.5
Costo total de rutas: 6
Promedio de pasos/dron: 3.0

Simulacion valida: 4 turno(s)
```

**Turn-by-turn breakdown:**

| Turn | Movement | Explanation |
|------|----------|-------------|
| 1 | `D1-waypoint1` | D1 moves forward, D2 waits (waypoint1 capacity=1) |
| 2 | `D1-waypoint2 D2-waypoint1` | D1 frees waypoint1, both advance |
| 3 | `D1-goal D2-waypoint2` | D1 arrives at goal, D2 advances |
| 4 | `D2-goal` | D2 arrives at goal, all delivered |

## Resources

- [Dijkstra's Algorithm - Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Python Documentation - argparse](https://docs.python.org/3/library/argparse.html)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/)
- [ANSI Escape Codes](https://en.wikipedia.org/wiki/ANSI_escape_code)

### AI Usage

AI was used for the following tasks during development:
- **Code documentation**: Generating docstrings and explaining implementation decisions.
- **Algorithm analysis**: Discussing time complexity and optimization strategies for the pathfinding algorithm.
- **Debugging**: Analyzing edge cases in the simulation engine, particularly around capacity constraint handling and restricted zone transit mechanics.
- **Code review**: Identifying potential improvements in code structure and type annotations.
