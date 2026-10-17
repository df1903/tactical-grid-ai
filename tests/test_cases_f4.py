"""Minimum demonstration cases 7 to 10 (enunciado section 13): expected vs. obtained.

All four use `caso_07_decision_adversarial.json`: 5x7 open map (camino, cost 1), two units per
side, default utility weights 10 / 3 / 1 / 0.5. Resource at (0,1); A1 (1,0), A2 (0,2),
B1 (1,2), B2 (2,4); A moves first. The metrics checked are the deterministic ones (everything
except time).
"""

from helpers import SCENARIOS
from tactical_grid.algorithms.adversarial import alpha_beta, minimax
from tactical_grid.algorithms.utility import Utility, UtilityWeights, make_utility
from tactical_grid.domain.model import Board, GameState, Move, Position
from tactical_grid.experiments.verifier import verify_adversarial
from tactical_grid.scenario.loader import load_scenario

GRAB = Move("A2", Position(0, 1))  # the nearest unit steps onto the resource
GUARD = Move("A1", Position(1, 1))  # the other unit takes the third neighbor of the resource


def _case() -> tuple[Board, GameState, Utility]:
    scenario = load_scenario(SCENARIOS / "caso_07_decision_adversarial.json")
    weights = UtilityWeights.from_mapping(scenario.utility_weights)
    utility = make_utility(scenario.board, scenario.initial_state.turn, weights)
    return scenario.board, scenario.initial_state, utility


def test_case_7_best_decision_is_not_to_grab_the_resource() -> None:
    # Greedy (depth 1) grabs: A2 -> (0,1) carries the resource next to the base (U = 3).
    # Depth 2 still prefers it but its value falls to 0: B1 steps next to the carrier and the
    # resource drops (interception). Depth 3 finds that moving A1 -> (1,1) first leaves B1 no
    # free cell adjacent to (0,1) before A2 grabs, so the carrier keeps it: U = 3 - 1 + 0.5 * 2.
    board, state, utility = _case()
    greedy = minimax(board, state, 1, utility)
    two_ply = minimax(board, state, 2, utility)
    decision = minimax(board, state, 3, utility, record=True)

    assert (greedy.action, greedy.value) == (GRAB, 3.0)
    assert (two_ply.action, two_ply.value) == (GRAB, 0.0)
    assert (decision.action, decision.value) == (GUARD, 3.0)
    values = dict(decision.root_values)
    assert values[GRAB] == 0.0
    assert max(value for action, value in values.items() if action != GUARD) == 0.0
    assert verify_adversarial(board, state, decision).ok


def test_case_8_alpha_beta_same_action_fewer_nodes() -> None:
    board, state, utility = _case()
    plain = minimax(board, state, 4, utility)
    pruned = alpha_beta(board, state, 4, utility, record=True)

    assert (pruned.action, pruned.value) == (plain.action, plain.value)
    assert (plain.generated, plain.evaluated, plain.pruned) == (4826, 4296, 0)
    assert (pruned.generated, pruned.evaluated, pruned.pruned) == (431, 299, 757)
    assert verify_adversarial(board, state, pruned).ok


def test_case_9_action_order_changes_the_amount_of_pruning() -> None:
    board, state, utility = _case()
    default = alpha_beta(board, state, 3, utility, "default")
    reverse = alpha_beta(board, state, 3, utility, "reversed")

    assert default.action == reverse.action == GUARD  # the decision does not depend on order
    assert default.value == reverse.value == 3.0
    assert (default.generated, default.evaluated, default.pruned) == (142, 110, 106)
    assert (reverse.generated, reverse.evaluated, reverse.pruned) == (191, 148, 145)


def test_case_10_depth_changes_effort_value_and_decision() -> None:
    # Odd depths end on A's move, so the guard looks safe; at even depths B gets one more reply
    # and every value flattens to 0, so the first action in order wins the tie.
    board, state, utility = _case()
    runs = {depth: alpha_beta(board, state, depth, utility) for depth in (1, 2, 3, 4, 5)}

    assert [(r.value, r.depth_reached) for r in runs.values()] == [
        (3.0, 1),
        (0.0, 2),
        (3.0, 3),
        (0.0, 4),
        (3.0, 5),
    ]
    assert [r.action for r in runs.values()] == [
        GRAB,
        GRAB,
        GUARD,
        Move("A1", Position(0, 0)),
        GUARD,
    ]
    assert [r.evaluated for r in runs.values()] == [7, 24, 110, 299, 1583]
