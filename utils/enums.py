from enum import Enum


# ENUMS
class ZoneType(Enum):
    """Tipos de zonas en la red de navegación.

    Atributos:
        NORMAL: Zona estándar con costo de 1 turno.
        RESTRICTED: Zona sensible con costo de 2 turnos.
        PRIORITY: Zona preferida con costo de 1 turno.
        BLOCKED: Zona inaccesible (no se puede entrar).
    """

    NORMAL = 1
    RESTRICTED = 2
    PRIORITY = 1
    BLOCKED = float('inf')


class DroneState(Enum):
    """Estados posibles de un dron durante la simulación.

    Atributos:
        IDLE: Dron esperando en una zona.
        MOVING: Dron en movimiento normal hacia siguiente zona.
        IN_TRANSIT: Dron en vuelo hacia zona restringida (ocupa conexión).
        DELIVERED: Dron ha llegado al destino final.
        WAITING: Dron bloqueado (capacidad llena o conflicto).
    """
    IDLE = "idle"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    WAITING = "waiting"


class Color(str, Enum):
    """Named CSS colors used by the game
    for terminal output and tinting."""

    ALICEBLUE = "aliceblue"
    ANTIQUEWHITE = "antiquewhite"
    AZURE = "azure"
    BEIGE = "beige"
    BISQUE = "bisque"
    BLANCHEDALMOND = "blanchedalmond"
    FLORALWHITE = "floralwhite"
    GHOSTWHITE = "ghostwhite"
    HONEYDEW = "honeydew"
    IVORY = "ivory"
    LAVENDERBLUSH = "lavenderblush"
    LAVENDER = "lavender"
    LINEN = "linen"
    MINTCREAM = "mintcream"
    MISTYROSE = "mistyrose"
    OLDLACE = "oldlace"
    SEASHELL = "seashell"
    SNOW = "snow"
    WHITESMOKE = "whitesmoke"
    WHITE = "white"

    BLACK = "black"
    GAINSBORO = "gainsboro"
    LIGHTGRAY = "lightgray"
    LIGHTGREY = "lightgrey"
    SILVER = "silver"
    DARKGRAY = "darkgray"
    DARKGREY = "darkgrey"
    GRAY = "gray"
    GREY = "grey"
    DIMGRAY = "dimgray"
    DIMGREY = "dimgrey"
    SLATEGRAY = "slategray"
    SLATEGREY = "slategrey"

    INDIANRED = "indianred"
    LIGHTCORAL = "lightcoral"
    SALMON = "salmon"
    DARKSALMON = "darksalmon"
    LIGHTSALMON = "lightsalmon"
    CRIMSON = "crimson"
    RED = "red"
    FIREBRICK = "firebrick"
    DARKRED = "darkred"
    PINK = "pink"
    LIGHTPINK = "lightpink"
    HOTPINK = "hotpink"
    DEEPPINK = "deeppink"
    PALEVIOLETRED = "palevioletred"
    MEDIUMVIOLETRED = "mediumvioletred"

    CORAL = "coral"
    TOMATO = "tomato"
    ORANGERED = "orangered"
    ORANGE = "orange"
    DARKORANGE = "darkorange"
    PEACHPUFF = "peachpuff"
    PAPAYAWHIP = "papayawhip"
    MOCCASIN = "moccasin"

    YELLOW = "yellow"
    LIGHTYELLOW = "lightyellow"
    LEMONCHIFFON = "lemonchiffon"
    LIGHTGOLDENRODYELLOW = "lightgoldenrodyellow"
    KHAKI = "khaki"
    DARKKHAKI = "darkkhaki"
    GOLD = "gold"
    GOLDENROD = "goldenrod"
    PALEGOLDENROD = "palegoldenrod"

    GREEN = "green"
    LIGHTGREEN = "lightgreen"
    DARKGREEN = "darkgreen"
    FORESTGREEN = "forestgreen"
    SEAGREEN = "seagreen"
    MEDIUMSEAGREEN = "mediumseagreen"
    LIGHTSEAGREEN = "lightseagreen"
    PALEGREEN = "palegreen"
    SPRINGGREEN = "springgreen"
    LAWNGREEN = "lawngreen"
    LIME = "lime"
    LIMEGREEN = "limegreen"
    CHARTREUSE = "chartreuse"
    OLIVE = "olive"
    OLIVEDRAB = "olivedrab"
    DARKOLIVEGREEN = "darkolivegreen"
    MEDIUMSPRINGGREEN = "mediumspringgreen"
    MEDIUMAQUAMARINE = "mediumaquamarine"
    AQUAMARINE = "aquamarine"
    TURQUOISE = "turquoise"
    MEDIUMTURQUOISE = "mediumturquoise"
    DARKSEAGREEN = "darkseagreen"
    GREENYELLOW = "greenyellow"

    AQUA = "aqua"
    CYAN = "cyan"
    LIGHTCYAN = "lightcyan"
    TEAL = "teal"
    DARKCYAN = "darkcyan"
    BLUE = "blue"
    LIGHTBLUE = "lightblue"
    SKYBLUE = "skyblue"
    LIGHTSKYBLUE = "lightskyblue"
    DEEPSKYBLUE = "deepskyblue"
    DODGERBLUE = "dodgerblue"
    CORNFLOWERBLUE = "cornflowerblue"
    STEELBLUE = "steelblue"
    ROYALBLUE = "royalblue"
    MIDNIGHTBLUE = "midnightblue"
    MEDIUMBLUE = "mediumblue"
    DARKBLUE = "darkblue"
    NAVY = "navy"
    PALETURQUOISE = "paleturquoise"
    LIGHTSTEELBLUE = "lightsteelblue"
    POWDERBLUE = "powderblue"

    PURPLE = "purple"
    VIOLET = "violet"
    BLUEVIOLET = "blueviolet"
    DARKVIOLET = "darkviolet"
    MEDIUMORCHID = "mediumorchid"
    ORCHID = "orchid"
    PLUM = "plum"
    MEDIUMPURPLE = "mediumpurple"
    INDIGO = "indigo"
    DARKORCHID = "darkorchid"
    DARKMAGENTA = "darkmagenta"
    MAGENTA = "magenta"
    FUCHSIA = "fuchsia"
    THISTLE = "thistle"

    BROWN = "brown"
    BURLYWOOD = "burlywood"
    CHOCOLATE = "chocolate"
    SADDLEBROWN = "saddlebrown"
    SIENNA = "sienna"
    PERU = "peru"
    TAN = "tan"
    ROSYBROWN = "rosybrown"
    SANDYBROWN = "sandybrown"
    WHEAT = "wheat"
