"""Minimum demonstration cases 7 to 10 (enunciado section 13): expected vs. obtained.

All four use `caso_07_decision_adversarial.json`: 20x20 map (camino, a few pantanos and a wall
with a gap), three units per side, default utility weights 10 / 3 / 1 / 0.5 / 0.5. Resource at
(8,11), neutral; A1 (9,11) and A3 (7,11) are both next to it, A2 (7,8); B1 (10,8), B2 (12,11),
B3 (12,8) come from the south; A moves first. The metrics checked are the deterministic ones
(everything except time).
"""

from helpers import SCENARIOS
from tactical_grid.algorithms.adversarial import alpha_beta, minimax
from tactical_grid.algorithms.utility import Utility, UtilityWeights, make_utility
from tactical_grid.domain.model import Board, GameState, Move, Position, Side
from tactical_grid.domain.rules import apply, is_terminal, skip_turn, winner
from tactical_grid.experiments.verifier import verify_adversarial
from tactical_grid.scenario.loader import load_scenario

RESOURCE = Position(8, 11)
GRAB_A1 = Move("A1", RESOURCE)  # the unit south of the resource steps onto it
GRAB_A3 = Move("A3", RESOURCE)  # the unit north of the resource steps onto it


def _case() -> tuple[Board, GameState, Utility]:
    scenario = load_scenario(SCENARIOS / "caso_07_decision_adversarial.json")
    weights = UtilityWeights.from_mapping(scenario.utility_weights)
    utility = make_utility(scenario.board, scenario.initial_state.turn, weights)
    return scenario.board, scenario.initial_state, utility


def test_case_7_deeper_search_breaks_the_tie_between_the_two_grabs() -> None:
    # Depth 1 and 2 cannot tell the two grabs apart (A1 and A3 are equally close), so the first
    # in action order wins. From depth 3 the rivals' approach is inside the horizon: grabbing with
    # A3 leaves A1 on the south side, between the carrier and the rivals (who come from the
    # south), and its value is clearly the best (-1.0 against -3.5 for everything else).
    board, state, utility = _case()
    greedy = minimax(board, state, 1, utility)
    two_ply = minimax(board, state, 2, utility)
    decision = minimax(board, state, 3, utility, record=True)

    assert (greedy.action, greedy.value) == (GRAB_A1, -2.5)
    assert dict(greedy.root_values)[GRAB_A3] == -2.5  # the same value at depth 1: a tie
    assert (two_ply.action, two_ply.value) == (GRAB_A1, -3.5)
    assert (decision.action, decision.value) == (GRAB_A3, -1.0)
    values = dict(decision.root_values)
    assert values[GRAB_A1] == -3.5
    assert max(value for action, value in values.items() if action != GRAB_A3) == -3.5
    assert verify_adversarial(board, state, decision).ok


def test_case_8_alpha_beta_same_action_fewer_nodes() -> None:
    board, state, utility = _case()
    plain = minimax(board, state, 4, utility)
    pruned = alpha_beta(board, state, 4, utility, record=True)

    assert (pruned.action, pruned.value) == (plain.action, plain.value) == (GRAB_A3, -2.0)
    assert (plain.generated, plain.evaluated, plain.pruned) == (14896, 13501, 0)
    assert (pruned.generated, pruned.evaluated, pruned.pruned) == (1440, 1064, 2557)
    assert verify_adversarial(board, state, pruned).ok


def test_case_9_action_order_changes_the_amount_of_pruning() -> None:
    board, state, utility = _case()
    default = alpha_beta(board, state, 3, utility, "default")
    reverse = alpha_beta(board, state, 3, utility, "reversed")

    assert default.action == reverse.action == GRAB_A3  # the decision does not depend on order
    assert default.value == reverse.value == -1.0
    assert (default.generated, default.evaluated, default.pruned) == (486, 412, 273)
    assert (reverse.generated, reverse.evaluated, reverse.pruned) == (304, 262, 153)


def test_case_10_depth_changes_effort_value_and_decision() -> None:
    # Depths 1 and 2 pick the first grab in order; from depth 3 the better one (A3) is found and
    # kept. The value changes with the horizon (even depths let B answer last) and the effort
    # grows about 6x per level.
    board, state, utility = _case()
    runs = {depth: alpha_beta(board, state, depth, utility) for depth in (1, 2, 3, 4, 5)}

    assert [(r.value, r.depth_reached) for r in runs.values()] == [
        (-2.5, 1),
        (-3.5, 2),
        (-1.0, 3),
        (-2.0, 4),
        (0.5, 5),
    ]
    assert [r.action for r in runs.values()] == [GRAB_A1, GRAB_A1, GRAB_A3, GRAB_A3, GRAB_A3]
    assert [r.evaluated for r in runs.values()] == [11, 25, 412, 1064, 7205]


def test_self_play_on_case_7_ends_with_a_delivery_instead_of_a_draw() -> None:
    # With the tackle as a deliberate action and the utility of moves-to-win, the game is
    # decided: both sides play alpha-beta at depth 3 and A delivers the resource.
    scenario = load_scenario(SCENARIOS / "caso_07_decision_adversarial.json")
    board, state = scenario.board, scenario.initial_state
    weights = UtilityWeights.from_mapping(scenario.utility_weights)
    while not is_terminal(board, state):
        utility = make_utility(board, state.turn, weights)
        action = alpha_beta(board, state, 3, utility).action
        state = skip_turn(state) if action is None else apply(board, state, action)[0]
    assert winner(board, state) is Side.A
    assert state.turn_number <= 45
