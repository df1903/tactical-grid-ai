"""Immutable data model of the game: board (static) and composite state (dynamic)."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum


# Enumeración para representar los lados del juego
class Side(Enum):
    A = "A"
    B = "B"

    # Lado contrario al actual
    @property
    def opponent(self) -> Side:
        return Side.B if self is Side.A else Side.A


# Clase para representar una posición en el tablero
@dataclass(frozen=True)
class Position:
    row: int
    col: int

    # Las 4 celdas vecinas, en orden arriba, abajo, izquierda, derecha
    def neighbors(self) -> tuple[Position, ...]:
        """Four orthogonal neighbors (up, down, left, right); no bounds check."""
        return (
            Position(self.row - 1, self.col),
            Position(self.row + 1, self.col),
            Position(self.row, self.col - 1),
            Position(self.row, self.col + 1),
        )

    # Dos posiciones son adyacentes si están a distancia Manhattan 1
    def is_adjacent(self, other: Position) -> bool:
        return abs(self.row - other.row) + abs(self.col - other.col) == 1


# Clase para representar el terreno del tablero
@dataclass(frozen=True)
class Terrain:
    """Terrain type. `cost` is None only when the terrain is not passable."""

    cost: float | None
    passable: bool


# Clase para representar el tablero
@dataclass(frozen=True, eq=False)
class Board:
    """Static part of a scenario: it never changes during a game."""

    rows: int
    cols: int
    grid: tuple[tuple[str, ...], ...]
    terrains: Mapping[str, Terrain]
    bases: Mapping[Side, Position]
    unit_sides: Mapping[str, Side]
    turn_limit: int

    # Indica si la posición está dentro del mapa
    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    # Terreno de la celda, buscado por su nombre en el catálogo del escenario
    def terrain_at(self, pos: Position) -> Terrain:
        return self.terrains[self.grid[pos.row][pos.col]]

    # Una celda es transitable si está en el mapa y su terreno lo permite
    def is_passable(self, pos: Position) -> bool:
        return self.in_bounds(pos) and self.terrain_at(pos).passable

    # Costo de entrar a la celda; falla si no es transitable
    def cost_at(self, pos: Position) -> float:
        cost = self.terrain_at(pos).cost
        if cost is None:
            raise ValueError(f"cell {pos} is not passable and has no cost")
        return cost


# Clase para representar el estado del juego
@dataclass(frozen=True)
class GameState:
    """Composite state (RF-10/RF-11).

    Two states with the same unit position are different when `carrier`, `resource`,
    `turn` or any other unit differs.
    """

    positions: tuple[tuple[str, Position], ...]  # sorted by unit id
    carrier: str | None
    resource: Position | None  # cell of the resource when nobody carries it
    turn: Side
    turn_number: int = 0

    # Posición de una unidad según su id
    def position_of(self, unit_id: str) -> Position:
        for uid, pos in self.positions:
            if uid == unit_id:
                return pos
        raise KeyError(unit_id)

    # Id de la unidad que ocupa la celda, o None si está libre
    def unit_at(self, pos: Position) -> str | None:
        for uid, upos in self.positions:
            if upos == pos:
                return uid
        return None


# Clase para representar un movimiento
@dataclass(frozen=True)
class Move:
    unit_id: str
    dest: Position


# Clase para representar un placaje: una unidad adyacente al portador rival le quita el recurso
@dataclass(frozen=True)
class Tackle:
    unit_id: str  # unidad que placa (no se mueve)
    target: str  # unidad rival que lleva el recurso


# Acciones posibles: mover una unidad o placar al portador rival
Action = Move | Tackle
