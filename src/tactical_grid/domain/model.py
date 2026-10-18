"""Immutable data model of the game: board (static) and composite state (dynamic)."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    A = "A"
    B = "B"

    @property
    def opponent(self) -> Side:
        return Side.B if self is Side.A else Side.A


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def neighbors(self) -> tuple[Position, ...]:
        """Four orthogonal neighbors (up, down, left, right); no bounds check."""
        return (
            Position(self.row - 1, self.col),
            Position(self.row + 1, self.col),
            Position(self.row, self.col - 1),
            Position(self.row, self.col + 1),
        )

    def is_adjacent(self, other: Position) -> bool:
        return abs(self.row - other.row) + abs(self.col - other.col) == 1


@dataclass(frozen=True)
class Terrain:
    """Terrain type. `cost` is None only when the terrain is not passable."""

    cost: float | None
    passable: bool


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

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def terrain_at(self, pos: Position) -> Terrain:
        return self.terrains[self.grid[pos.row][pos.col]]

    def is_passable(self, pos: Position) -> bool:
        return self.in_bounds(pos) and self.terrain_at(pos).passable

    def cost_at(self, pos: Position) -> float:
        cost = self.terrain_at(pos).cost
        if cost is None:
            raise ValueError(f"cell {pos} is not passable and has no cost")
        return cost


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

    def position_of(self, unit_id: str) -> Position:
        for uid, pos in self.positions:
            if uid == unit_id:
                return pos
        raise KeyError(unit_id)

    def unit_at(self, pos: Position) -> str | None:
        for uid, upos in self.positions:
            if upos == pos:
                return uid
        return None


@dataclass(frozen=True)
class Move:
    unit_id: str
    dest: Position


Action = Move
