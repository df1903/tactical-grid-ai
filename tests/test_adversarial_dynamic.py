from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from helpers import SCENARIOS
from tactical_grid.algorithms.adversarial import ActionOrder
from tactical_grid.algorithms.adversarial_dynamic import (
    DynamicAdversarialResult,
    alpha_beta_dynamic,
    minimax_dynamic,
)
from tactical_grid.algorithms.utility import UtilityWeights
from tactical_grid.algorithms.utility_dynamic import DynamicUtility, make_dynamic_utility
from tactical_grid.domain.dynamic import (
    DynamicState,
    initial_dynamic_state,
    legal_actions,
    pass_turn,
)
from tactical_grid.domain.model import Board, Move, Position, Tackle
from tactical_grid.experiments.verifier import verify_adversarial_dynamic
from tactical_grid.scenario.loader import DEFAULT_UTILITY_WEIGHTS, Scenario, load_scenario
from test_dynamic_rules import RULES, STEAL, Unit, make, with_recovery

CASE_7 = SCENARIOS / "caso_07_decision_adversarial.json"
LARGE = [SCENARIOS / "prueba_20x20.json", SCENARIOS / "caso_03_obstaculo_heuristica.json"]
Algorithm = Callable[..., DynamicAdversarialResult]


def _utility(scenario: Scenario) -> DynamicUtility:
    weights = UtilityWeights.from_mapping(scenario.utility_weights)
    return make_dynamic_utility(scenario.board, scenario.initial_state.turn, weights)


@pytest.mark.parametrize("depth", [1, 2, 3])
@pytest.mark.parametrize("order", ["default", "reversed"])
def test_alpha_beta_matches_minimax_on_case_7(depth: int, order: ActionOrder) -> None:
    scenario = load_scenario(CASE_7)
    state = initial_dynamic_state(scenario.initial_state)
    utility = _utility(scenario)
    args = (scenario.board, state, depth, utility, scenario.dynamic_rules, order)
    full = minimax_dynamic(*args)
    pruned = alpha_beta_dynamic(*args)
    assert (pruned.value, pruned.action) == (full.value, full.action)
    assert full.pruned == 0
    assert pruned.generated <= full.generated


@pytest.mark.parametrize("path", LARGE)
def test_alpha_beta_matches_minimax_on_large_maps(path: Path) -> None:
    scenario = load_scenario(path)
    state = initial_dynamic_state(scenario.initial_state)
    utility = _utility(scenario)
    args = (scenario.board, state, 3, utility, scenario.dynamic_rules)
    full = minimax_dynamic(*args)
    pruned = alpha_beta_dynamic(*args)
    assert (pruned.value, pruned.action) == (full.value, full.action)


def _small() -> tuple[Board, DynamicState, DynamicUtility]:
    units: list[Unit] = [("A1", "A", 2, 2), ("A2", "A", 3, 0), ("B1", "B", 4, 3), ("B2", "B", 0, 4)]
    board, state = make(units, resource=(0, 3), special={(1, 2): "pantano"})
    weights = UtilityWeights.from_mapping(DEFAULT_UTILITY_WEIGHTS)
    return board, state, make_dynamic_utility(board, state.turn, weights)


@pytest.mark.parametrize("algorithm", [minimax_dynamic, alpha_beta_dynamic])
def test_only_legal_dynamic_actions_are_considered(algorithm: Algorithm) -> None:
    board, state, utility = _small()
    state = with_recovery(state, A1=2)
    result = algorithm(board, state, 3, utility, RULES, record=True)
    assert result.considered
    assert all(action in legal_actions(board, node) for node, action in result.considered)
    assert all(
        getattr(action, "unit_id", "") != "A1"
        for node, action in result.considered
        if node is state
    )
    assert verify_adversarial_dynamic(board, state, result).ok


def test_the_verifier_rejects_a_move_of_a_unit_in_recovery() -> None:
    board, state, utility = _small()
    state = with_recovery(state, A1=2)
    result = minimax_dynamic(board, state, 1, utility, RULES, record=True)
    illegal = Move("A1", Position(2, 1))
    forged = replace(result, considered=((state, illegal),), action=illegal)
    assert not verify_adversarial_dynamic(board, state, forged).ok


def test_the_verifier_requires_recorded_actions() -> None:
    board, state, utility = _small()
    result = minimax_dynamic(board, state, 1, utility, RULES)
    assert not verify_adversarial_dynamic(board, state, result).ok


@pytest.mark.parametrize("algorithm", [minimax_dynamic, alpha_beta_dynamic])
def test_a_blocked_root_has_no_action_and_the_value_of_passing(algorithm: Algorithm) -> None:
    board, state, utility = _small()
    state = with_recovery(state, A1=2, A2=2)
    result = algorithm(board, state, 1, utility, RULES)
    passed = pass_turn(board, state)
    assert result.action is None
    assert result.value == utility(passed)


@pytest.mark.parametrize("algorithm", [minimax_dynamic, alpha_beta_dynamic])
def test_a_blocked_node_is_not_a_leaf(algorithm: Algorithm) -> None:
    board, state, utility = _small()
    state = with_recovery(state, A1=1, A2=1)
    state = replace(state, base=replace(state.base, turn=state.base.turn.opponent))
    result = algorithm(board, state, 3, utility, RULES)
    # profundidad 3: B juega, A pasa (nodo de un hijo) y B juega otra vez
    assert result.depth_reached == 3


def test_the_search_considers_the_steal() -> None:
    board, state = make(STEAL, carrier="A1", turn="B")
    weights = UtilityWeights.from_mapping(DEFAULT_UTILITY_WEIGHTS)
    utility = make_dynamic_utility(board, state.turn, weights)
    result = alpha_beta_dynamic(board, state, 2, utility, RULES)
    assert Tackle("B1", "A1") in [action for action, _ in result.root_values]


def test_depth_must_be_positive() -> None:
    board, state, utility = _small()
    with pytest.raises(ValueError):
        minimax_dynamic(board, state, 0, utility, RULES)
