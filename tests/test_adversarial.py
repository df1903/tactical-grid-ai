import math
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from helpers import APENDICE_A, SCENARIOS
from tactical_grid.algorithms.adversarial import ActionOrder, AdversarialResult, alpha_beta, minimax
from tactical_grid.algorithms.utility import Utility, UtilityWeights, make_utility
from tactical_grid.domain.model import Move, Position
from tactical_grid.domain.rules import legal_actions
from tactical_grid.experiments.verifier import verify_adversarial
from tactical_grid.scenario.loader import Scenario, TestConfig, load_scenario
from test_domain_rules import make

CASE_7 = SCENARIOS / "caso_07_decision_adversarial.json"
FILES = [APENDICE_A, CASE_7]
Algorithm = Callable[..., AdversarialResult]


def _utility(scenario: Scenario) -> Utility:
    weights = UtilityWeights.from_mapping(scenario.utility_weights)
    return make_utility(scenario.board, scenario.initial_state.turn, weights)


@pytest.mark.parametrize("path", FILES)
@pytest.mark.parametrize("depth", [1, 2, 3])
@pytest.mark.parametrize("order", ["default", "reversed"])
def test_alpha_beta_matches_minimax(path: Path, depth: int, order: ActionOrder) -> None:
    scenario = load_scenario(path)
    board, state, utility = scenario.board, scenario.initial_state, _utility(scenario)
    full = minimax(board, state, depth, utility, order)
    pruned = alpha_beta(board, state, depth, utility, order)
    assert (pruned.action, pruned.value) == (full.action, full.value)
    assert pruned.generated <= full.generated
    assert pruned.evaluated <= full.evaluated
    assert full.pruned == 0
    assert full.depth_reached == pruned.depth_reached == depth


def test_depth_one_picks_the_best_immediate_successor() -> None:
    scenario = load_scenario(APENDICE_A)
    board, state, utility = scenario.board, scenario.initial_state, _utility(scenario)
    result = minimax(board, state, 1, utility)
    assert result.generated == result.evaluated == len(legal_actions(board, state))
    assert result.value == max(value for _, value in result.root_values)


def test_terminal_root_has_no_action() -> None:
    scenario = load_scenario(APENDICE_A)
    board = replace(scenario.board, turn_limit=0)
    result = alpha_beta(board, scenario.initial_state, 3, _utility(scenario))
    assert result.action is None
    assert (result.generated, result.evaluated, result.depth_reached) == (0, 1, 0)


def test_a_delivery_is_found_and_valued_above_everything_else() -> None:
    scenario = load_scenario(CASE_7)
    # A1 carries the resource and stands next to its base: moving onto the base wins.
    state = replace(scenario.initial_state, carrier="A1", resource=None)
    result = minimax(scenario.board, state, 4, _utility(scenario))
    assert result.action == Move("A1", Position(0, 0))
    assert result.value > 10.0


def test_depth_must_be_positive() -> None:
    scenario = load_scenario(APENDICE_A)
    with pytest.raises(ValueError):
        minimax(scenario.board, scenario.initial_state, 0, _utility(scenario))


@pytest.mark.parametrize("algorithm", [minimax, alpha_beta])
def test_only_legal_actions_are_considered(algorithm: Algorithm) -> None:
    scenario = load_scenario(CASE_7)
    board, state, utility = scenario.board, scenario.initial_state, _utility(scenario)
    result = algorithm(board, state, 3, utility, record=True)
    assert len(result.considered) == result.generated
    assert verify_adversarial(board, state, result).ok


def test_verifier_rejects_an_illegal_action() -> None:
    scenario = load_scenario(CASE_7)
    board, state, utility = scenario.board, scenario.initial_state, _utility(scenario)
    result = minimax(board, state, 2, utility, record=True)
    # B moves are illegal at the root, where A is the side to move.
    bad_action = legal_actions(board, replace(state, turn=state.turn.opponent))[0]
    tampered = replace(result, considered=((state, bad_action), *result.considered))
    report = verify_adversarial(board, state, tampered)
    assert not report.ok
    assert not report.checks[0].passed


def test_verifier_requires_recorded_actions() -> None:
    scenario = load_scenario(CASE_7)
    board, state, utility = scenario.board, scenario.initial_state, _utility(scenario)
    report = verify_adversarial(board, state, minimax(board, state, 2, utility))
    assert not report.checks[0].passed


def test_blocked_side_node_is_evaluated_as_a_leaf() -> None:
    # After any A move, B1 (cornered by A2 and A3) has no move: its turn is skipped.
    board, state = make(
        [("A1", "A", 2, 2), ("A2", "A", 0, 1), ("A3", "A", 1, 0), ("B1", "B", 0, 0)],
        resource=(3, 3),
    )
    scenario = Scenario(board, state, TestConfig(None, None, None, None))
    for algorithm in (minimax, alpha_beta):
        result = algorithm(board, state, 3, _utility(scenario))
        assert result.action is not None
        assert math.isfinite(result.value)
