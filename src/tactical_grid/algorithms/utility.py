"""Utility (evaluation) function for the adversarial search (RF-27).

The utility is always measured from one side, MAX: MAX maximizes it and MIN minimizes it.
Weights are read from the scenario (`utilidad` section), never written here.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from tactical_grid.domain.model import Board, GameState, Position, Side
from tactical_grid.domain.rules import winner

Utility = Callable[[GameState], float]


@dataclass(frozen=True)
class UtilityWeights:
    delivery: float
    carry: float
    goal_distance: float
    rival_distance: float

    @classmethod
    def from_mapping(cls, values: Mapping[str, float]) -> UtilityWeights:
        return cls(
            delivery=values["delivery"],
            carry=values["carry"],
            goal_distance=values["goal_distance"],
            rival_distance=values["rival_distance"],
        )


def _distance(a: Position, b: Position) -> int:
    return abs(a.row - b.row) + abs(a.col - b.col)


def make_utility(board: Board, max_side: Side, weights: UtilityWeights) -> Utility:
    """Build the utility `U(state)` seen from `max_side`.

    Purpose: score a state for Minimax / alpha-beta as
        U = w_delivery * (+1 if MAX delivered, -1 if MIN delivered)
          + w_carry * (+1 if MAX carries the resource, -1 if MIN carries it)
          - w_goal * (distance to the current objective)
          + w_rival * (distance of the nearest rival to the carrier, only if MAX carries).
        Objective: MAX's base if MAX carries; the carrier if MIN carries (chase it); the
        resource cell otherwise. Distance is Manhattan from the nearest MAX unit (from the
        carrier itself when MAX carries). A rival near MAX's carrier lowers U (interception).
    Preconditions: `state` belongs to `board`; weights are non-negative.
    Postconditions: deterministic and side-effect free; terminal wins dominate the other
        terms with the scenario's weights (delivery outweighs carry plus any rival bonus).
    Complexity: O(U) per evaluation for U units.
    AI usage: Claude Code (Sonnet 5.5) drafted the function from the 2026-10-16 decision.
    AI intervention: the sign of the rival term follows the carrier's side (the decision
        text gave a single negative term); when MIN carries it is omitted because the
        goal-distance term already measures the chase.
    Student validation: pending cross-review by the other team member.
    """

    def utility(state: GameState) -> float:
        score = 0.0
        won = winner(board, state)
        if won is not None:
            score += weights.delivery if won is max_side else -weights.delivery
        mine = [pos for uid, pos in state.positions if board.unit_sides[uid] is max_side]
        theirs = [pos for uid, pos in state.positions if board.unit_sides[uid] is not max_side]
        if state.carrier is None:
            assert state.resource is not None
            score -= weights.goal_distance * min(_distance(p, state.resource) for p in mine)
            return score
        carrier_pos = state.position_of(state.carrier)
        if board.unit_sides[state.carrier] is max_side:
            score += weights.carry
            score -= weights.goal_distance * _distance(carrier_pos, board.bases[max_side])
            score += weights.rival_distance * min(_distance(p, carrier_pos) for p in theirs)
        else:
            score -= weights.carry
            score -= weights.goal_distance * min(_distance(p, carrier_pos) for p in mine)
        return score

    return utility
