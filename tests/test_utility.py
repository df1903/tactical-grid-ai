from dataclasses import replace

from helpers import APENDICE_A, SCENARIOS
from tactical_grid.algorithms.utility import UtilityWeights, make_utility
from tactical_grid.domain.model import GameState, Position, Side
from tactical_grid.scenario.loader import load_scenario

W = UtilityWeights(delivery=10.0, carry=3.0, goal_distance=1.0, rival_distance=0.5)


def _move(state: GameState, unit: str, row: int, col: int) -> GameState:
    positions = tuple((u, Position(row, col) if u == unit else p) for u, p in state.positions)
    return replace(state, positions=positions)


def test_free_resource_penalizes_distance_of_nearest_max_unit() -> None:
    scenario = load_scenario(SCENARIOS / "caso_07_decision_adversarial.json")
    board, state = scenario.board, scenario.initial_state
    utility = make_utility(board, Side.A, W)
    # resource (0,1): A2 at (0,2) is the nearest MAX unit, distance 1.
    assert utility(state) == -1.0
    assert utility(_move(state, "A2", 0, 1)) == 0.0  # standing on it, nobody carries yet


def test_max_carrier_gets_carry_bonus_minus_distance_plus_rival_gap() -> None:
    scenario = load_scenario(SCENARIOS / "caso_07_decision_adversarial.json")
    board, state = scenario.board, scenario.initial_state
    carrying = replace(_move(state, "A2", 0, 1), carrier="A2", resource=None)
    # carry +3, distance (0,1)->(0,0) is 1, nearest rival B1 (1,2) is 2 away: +0.5 * 2
    assert make_utility(board, Side.A, W)(carrying) == 3.0 - 1.0 + 1.0


def test_utility_is_antisymmetric_in_the_carry_and_delivery_terms() -> None:
    scenario = load_scenario(SCENARIOS / "caso_07_decision_adversarial.json")
    board, state = scenario.board, scenario.initial_state
    b1_carries = replace(state, carrier="B1", resource=None)
    # carry -3, MAX chases the carrier B1 (1,2): nearest MAX unit A2 (0,2) is 1 away
    assert make_utility(board, Side.A, W)(b1_carries) == -3.0 - 1.0
    delivered = replace(_move(state, "A1", 0, 0), carrier="A1", resource=None)
    assert make_utility(board, Side.A, W)(delivered) > 10.0  # delivery dominates
    assert make_utility(board, Side.B, W)(delivered) < -10.0


def test_weights_change_the_value() -> None:
    scenario = load_scenario(APENDICE_A)
    board, state = scenario.board, scenario.initial_state
    heavy = UtilityWeights(delivery=10.0, carry=3.0, goal_distance=2.0, rival_distance=0.5)
    base = make_utility(board, Side.A, W)(state)
    assert make_utility(board, Side.A, heavy)(state) == 2 * base
