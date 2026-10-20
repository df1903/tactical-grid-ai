"""Utility for the dynamic variant: the same idea as `utility.py`, measured in own turns.

In the variant a unit that enters a cell of cost c is busy for `ceil(c)` of its side's turns, so
the number of steps does not tell how soon a side delivers. Here every distance is the sum of
`ceil(cost)` of the cells entered, and the turns a unit still has to wait are added to it. The
base utility (`utility.py`) is not modified. Weights still come from the scenario.
"""

import heapq
import math
from collections.abc import Callable

from tactical_grid.algorithms.utility import UtilityWeights
from tactical_grid.domain.dynamic import DynamicState
from tactical_grid.domain.model import Board, Position, Side
from tactical_grid.domain.rules import winner

# Tipo de la utilidad de la variante: recibe el estado dinámico y devuelve el puntaje para MAX
DynamicUtility = Callable[[DynamicState], float]


# Distancias en turnos propios sobre el mapa real, calculadas una vez por destino
class _TurnDistances:
    """Fewest own turns between cells, ignoring units; cached per target cell."""

    def __init__(self, board: Board) -> None:
        self.board = board
        self.weights = {
            Position(r, c): math.ceil(board.cost_at(Position(r, c)))
            for r in range(board.rows)
            for c in range(board.cols)
            if board.is_passable(Position(r, c))
        }
        # una celda imposible de alcanzar cuenta como recorrer todo el mapa por el terreno más caro
        self.unreachable = board.rows * board.cols * max(self.weights.values(), default=1)
        self.cheapest = min(self.weights.values(), default=1)
        self._fields: dict[tuple[Side, Position], dict[Position, int]] = {}

    # Turnos de `a` a `b` para las unidades de `side` (no pueden pisar la base rival)
    def __call__(self, side: Side, a: Position, b: Position) -> int:
        field = self._fields.get((side, b))
        if field is None:
            field = self._dijkstra(side, b)
            self._fields[(side, b)] = field
        return field.get(a, self.unreachable)

    # Turnos que cuesta entrar a la celda
    def entering(self, cell: Position) -> int:
        return self.weights[cell]

    # Dijkstra desde el destino: llegar a `c` desde un vecino cuesta lo que pesa entrar a `c`
    def _dijkstra(self, side: Side, target: Position) -> dict[Position, int]:
        banned = self.board.bases[side.opponent]
        if target == banned:
            return {}
        best = {target: 0}
        queue = [(0, target.row, target.col)]
        while queue:
            turns, row, col = heapq.heappop(queue)
            cell = Position(row, col)
            if turns > best[cell]:
                continue
            for nxt in cell.neighbors():
                if nxt == banned or nxt not in self.weights:
                    continue
                total = turns + self.weights[cell]
                if total < best.get(nxt, total + 1):
                    best[nxt] = total
                    heapq.heappush(queue, (total, nxt.row, nxt.col))
        return best


# Función para construir la utilidad U(estado) de la variante vista desde el lado MAX
def make_dynamic_utility(board: Board, max_side: Side, weights: UtilityWeights) -> DynamicUtility:
    """Build the utility `U(state)` of the dynamic variant seen from `max_side`.

    Purpose: score a state by how many own turns each side still needs to deliver, so that a
        search sees that entering expensive terrain now is not the same as doing it later.
        U = w_rival_progress * finish(MIN) - w_goal * finish(MAX)
          + w_carry * (+1 if MAX carries, -1 if MIN carries)
          + w_rival * (turns of the closest chaser to the carrier; +/- as carry).
        `finish(side)` is the base estimate with two changes: distances are sums of
        `ceil(cost)` of the entered cells (the same rule as the recovery) and the recovery turns
        the acting unit still has to wait are added to its distance. Terminal states are worth
        more than any other (bound derived from the board and the weights) and a draw is 0.
    Preconditions: `state` belongs to `board`; weights are non-negative.
    Postconditions: deterministic and side-effect free; with only cost-1 terrain and no unit in
        recovery it equals the base utility.
    Complexity: O(U) per evaluation after one Dijkstra per distinct target cell
        (O(R * C * log(R * C)) each, cached for the whole game).
    AI usage: Yes. Claude Code (Sonnet 5.5) wrote it on 2026-10-19 after a self-play bug: with
        step distances the search postponed advancing into expensive terrain forever.
    AI intervention: none after the draft.
    Student validation: tests/test_utility_dynamic.py checks equality with the base utility on
        cost-1 maps, that waiting is worse than advancing into expensive terrain, the recovery
        term and that the weights change the value.
    """
    turns = _TurnDistances(board)
    entries = {
        side: [cell for cell in base.neighbors() if board.is_passable(cell)]
        for side, base in board.bases.items()
    }
    longest = 3 * turns.unreachable + 3
    bound = (
        (weights.goal_distance + weights.rival_progress) * longest
        + weights.carry
        + weights.rival_distance * turns.unreachable
    )
    win_value = bound + weights.delivery

    # 2 turnos extra si todas las entradas libres de la base del bando están ocupadas
    def blocked(side: Side, state: DynamicState, carrier_pos: Position | None) -> int:
        cells = entries[side]
        if carrier_pos in cells:
            return 0
        occupied = {pos for uid, pos in state.base.positions if uid != state.base.carrier}
        return 2 if cells and all(cell in occupied for cell in cells) else 0

    # Turnos estimados que le faltan al bando para entregar el recurso
    def finish(side: Side, state: DynamicState, units: list[tuple[str, Position]]) -> int:
        base = state.base
        goal = board.bases[side]
        if base.carrier is None:
            assert base.resource is not None
            res = base.resource
            # quien está sobre el recurso no lo recoge: debe salir y volver (2 turnos como mínimo)
            reach = min(
                (turns(side, pos, res) or 2 * turns.cheapest) + state.recovery_of(uid)
                for uid, pos in units
            )
            return reach + turns(side, res, goal) + blocked(side, state, None)
        carrier_pos = base.position_of(base.carrier)
        if board.unit_sides[base.carrier] is side:
            own = state.recovery_of(base.carrier)
            return own + turns(side, carrier_pos, goal) + blocked(side, state, carrier_pos)
        # el rival lo lleva: llegar a su lado, placarlo y llevarlo desde ahí
        chase = min(
            max(turns(side, pos, carrier_pos) - turns.entering(carrier_pos), 0)
            + state.recovery_of(uid)
            for uid, pos in units
        )
        return chase + 1 + turns(side, carrier_pos, goal) + blocked(side, state, None)

    def utility(state: DynamicState) -> float:
        base = state.base
        won = winner(board, base)
        if won is not None:
            value = win_value + (board.turn_limit - base.turn_number)
            return value if won is max_side else -value
        if base.turn_number >= board.turn_limit:
            return 0.0
        mine: list[tuple[str, Position]] = []
        theirs: list[tuple[str, Position]] = []
        for uid, pos in base.positions:
            (mine if board.unit_sides[uid] is max_side else theirs).append((uid, pos))
        min_side = max_side.opponent
        score = weights.rival_progress * finish(min_side, state, theirs)
        score -= weights.goal_distance * finish(max_side, state, mine)
        if base.carrier is not None:
            # quien lleva el recurso suma por llevarlo y por tener lejos a sus perseguidores
            carrier_pos = base.position_of(base.carrier)
            carrier_side = board.unit_sides[base.carrier]
            chasers = theirs if carrier_side is max_side else mine
            gap = min(turns(carrier_side.opponent, pos, carrier_pos) for _, pos in chasers)
            sign = 1.0 if carrier_side is max_side else -1.0
            score += sign * (weights.carry + weights.rival_distance * gap)
        return score

    return utility
