"""Utility (evaluation) function for the adversarial search (RF-27).

The utility is always measured from one side, MAX: MAX maximizes it and MIN minimizes it.
Weights are read from the scenario (`utilidad` section), never written here.
"""

from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from tactical_grid.domain.model import Board, GameState, Position, Side
from tactical_grid.domain.rules import winner

# Tipo de la función de utilidad: recibe un estado y devuelve su puntaje para MAX
Utility = Callable[[GameState], float]


# Clase para guardar los pesos de cada término de la utilidad
@dataclass(frozen=True)
class UtilityWeights:
    delivery: float  # peso por entregar el recurso
    carry: float  # peso por llevar el recurso
    goal_distance: float  # peso de los pasos que le faltan a MAX para ganar
    rival_distance: float  # peso de la distancia del rival más cercano al portador
    rival_progress: float  # peso de los pasos que le faltan al rival para ganar

    # Construye los pesos a partir de un diccionario (el que viene del escenario)
    @classmethod
    def from_mapping(cls, values: Mapping[str, float]) -> UtilityWeights:
        return cls(
            delivery=values["delivery"],
            carry=values["carry"],
            goal_distance=values["goal_distance"],
            rival_distance=values["rival_distance"],
            rival_progress=values["rival_progress"],
        )


# Distancias en pasos sobre el mapa real (muros incluidos), calculadas una vez por destino
class _StepDistances:
    """Fewest moves between cells for one side, ignoring units; cached per target cell."""

    def __init__(self, board: Board) -> None:
        self.board = board
        # una celda imposible de alcanzar cuenta como recorrer todo el mapa
        self.unreachable = board.rows * board.cols
        self._fields: dict[tuple[Side, Position], dict[Position, int]] = {}

    # Pasos de `a` a `b` para las unidades de `side` (no pueden pisar la base rival)
    def __call__(self, side: Side, a: Position, b: Position) -> int:
        field = self._fields.get((side, b))
        if field is None:
            field = self._bfs(side, b)
            self._fields[(side, b)] = field
        return field.get(a, self.unreachable)

    # BFS desde el destino; los movimientos son simétricos, así que sirve para cualquier origen
    def _bfs(self, side: Side, target: Position) -> dict[Position, int]:
        banned = self.board.bases[side.opponent]
        if target == banned:
            return {}
        steps = {target: 0}
        queue = deque([target])
        while queue:
            cell = queue.popleft()
            for nxt in cell.neighbors():
                if nxt not in steps and nxt != banned and self.board.is_passable(nxt):
                    steps[nxt] = steps[cell] + 1
                    queue.append(nxt)
        return steps


# Función para construir la utilidad U(estado) vista desde el lado MAX
def make_utility(board: Board, max_side: Side, weights: UtilityWeights) -> Utility:
    """Build the utility `U(state)` seen from `max_side`.

    Purpose: score a state for Minimax / alpha-beta by how close each side is to winning:
        U = w_rival_progress * finish(MIN) - w_goal * finish(MAX)
          + w_carry * (+1 if MAX carries, -1 if MIN carries)
          + w_rival * (steps from the carrier to the nearest unit chasing it; +/- as carry).
        `finish(side)` estimates the moves the side still needs to deliver, with real step
        distances on the map (walls and the rival base cannot be crossed, units ignored):
          - nobody carries: nearest own unit to the resource (2 if it stands on it, since it
            must leave and come back) plus resource to own base;
          - own side carries: carrier to own base;
          - rival carries: nearest own unit until adjacent to the carrier, 1 for the tackle,
            plus carrier cell to own base.
        Each estimate adds 2 when every free entry of the own base is occupied (someone must
        make way first). Terminal states: a win is worth more than any non-terminal state
        (bound derived from the board and the weights) and sooner wins are worth more;
        a draw is worth 0.
    Preconditions: `state` belongs to `board`; weights are non-negative.
    Postconditions: deterministic and side-effect free. Picking the resource up never lowers
        the value of the side that picks it (the estimate is continuous across the pickup).
    Complexity: O(U) per evaluation for U units after one BFS per distinct target cell
        (O(R * C) each, cached for the whole game).
    AI usage: Yes. Claude Code (Opus 5.5) redesigned the function on 2026-10-18 after full-game
        simulations: the previous version ended every game on a 20x20 map in a draw.
    AI intervention: none after the redesign.
    Student validation: tests/test_utility.py checks the free-resource comparison, the pick-up
        bonus, distances around walls, the uncrossable rival base, zero-sum with equal weights,
        win/draw values and that the weights change the value; the earlier version was discarded
        after full-game simulations ended in draws.
    """
    steps = _StepDistances(board)
    entries = {
        side: [cell for cell in base.neighbors() if board.is_passable(cell)]
        for side, base in board.bases.items()
    }
    # cota de cualquier estado no terminal: un triunfo siempre vale más
    longest = 3 * steps.unreachable + 3
    bound = (
        (weights.goal_distance + weights.rival_progress) * longest
        + weights.carry
        + weights.rival_distance * steps.unreachable
    )
    win_value = bound + weights.delivery

    # 2 pasos extra si todas las entradas libres de la base del bando están ocupadas
    def blocked(side: Side, state: GameState, carrier_pos: Position | None) -> int:
        cells = entries[side]
        if carrier_pos in cells:
            return 0
        occupied = {pos for uid, pos in state.positions if uid != state.carrier}
        return 2 if cells and all(cell in occupied for cell in cells) else 0

    # Pasos estimados que le faltan al bando para entregar el recurso
    def finish(side: Side, state: GameState, units: list[Position]) -> int:
        base = board.bases[side]
        if state.carrier is None:
            assert state.resource is not None
            res = state.resource
            # quien está sobre el recurso no lo recoge: debe salir y volver (2 pasos)
            reach = min(steps(side, pos, res) or 2 for pos in units)
            return reach + steps(side, res, base) + blocked(side, state, None)
        carrier_pos = state.position_of(state.carrier)
        if board.unit_sides[state.carrier] is side:
            return steps(side, carrier_pos, base) + blocked(side, state, carrier_pos)
        # el rival lo lleva: llegar a su lado, placarlo y llevarlo desde ahí
        chase = min(max(steps(side, pos, carrier_pos) - 1, 0) for pos in units)
        return chase + 1 + steps(side, carrier_pos, base) + blocked(side, state, None)

    def utility(state: GameState) -> float:
        # estado terminal: triunfo (antes vale más), derrota o empate
        won = winner(board, state)
        if won is not None:
            value = win_value + (board.turn_limit - state.turn_number)
            return value if won is max_side else -value
        if state.turn_number >= board.turn_limit:
            return 0.0
        mine: list[Position] = []
        theirs: list[Position] = []
        for uid, pos in state.positions:
            (mine if board.unit_sides[uid] is max_side else theirs).append(pos)
        min_side = max_side.opponent
        score = weights.rival_progress * finish(min_side, state, theirs)
        score -= weights.goal_distance * finish(max_side, state, mine)
        if state.carrier is not None:
            # quien lleva el recurso suma por llevarlo y por tener lejos a sus perseguidores
            carrier_pos = state.position_of(state.carrier)
            carrier_side = board.unit_sides[state.carrier]
            chasers = theirs if carrier_side is max_side else mine
            gap = min(steps(carrier_side.opponent, pos, carrier_pos) for pos in chasers)
            sign = 1.0 if carrier_side is max_side else -1.0
            score += sign * (weights.carry + weights.rival_distance * gap)
        return score

    return utility
