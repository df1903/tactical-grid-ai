from dataclasses import replace

from helpers import APENDICE_A, SCENARIOS, mini_race
from tactical_grid.algorithms.utility import UtilityWeights, _StepDistances, make_utility
from tactical_grid.domain.model import GameState, Move, Position, Side
from tactical_grid.domain.rules import apply
from tactical_grid.scenario.loader import load_scenario

W = UtilityWeights(
    delivery=10.0, carry=3.0, goal_distance=1.0, rival_distance=0.5, rival_progress=0.5
)
CASE_3 = SCENARIOS / "caso_03_obstaculo_heuristica.json"


def _move(state: GameState, unit: str, row: int, col: int) -> GameState:
    positions = tuple((u, Position(row, col) if u == unit else p) for u, p in state.positions)
    return replace(state, positions=positions)


def test_free_resource_compares_the_moves_each_side_still_needs() -> None:
    scenario = mini_race()
    board, state = scenario.board, scenario.initial_state
    # A: A2 (0,2) is 1 step from the resource (0,1), which is 1 step from base (0,0) -> 2.
    # B: B1 (1,2) is 2 steps away, then 4 + 5 = 9 to base (4,6) -> 11.
    assert make_utility(board, Side.A, W)(state) == 0.5 * 11 - 2


def test_picking_the_resource_up_raises_the_value_of_the_picker() -> None:
    scenario = mini_race()
    board, state = scenario.board, scenario.initial_state
    utility = make_utility(board, Side.A, W)
    carrying, _ = apply(board, state, Move("A2", Position(0, 1)))
    assert carrying.carrier == "A2"
    # A: 1 step home. B: B1 needs 1 step to get next to A2, 1 tackle, 9 home -> 11.
    # carry +3 and the nearest chaser B1 is 2 steps away: +0.5 * 2.
    assert utility(carrying) == 0.5 * 11 - 1 + 3 + 1
    assert utility(carrying) > utility(state)


def test_distances_follow_the_real_map_around_walls() -> None:
    scenario = load_scenario(CASE_3)  # wall on column 8, rows 0-15
    steps = _StepDistances(scenario.board)
    left, right = Position(5, 5), Position(5, 10)
    manhattan = abs(left.row - right.row) + abs(left.col - right.col)
    assert steps(Side.A, left, right) > manhattan
    assert steps(Side.A, left, right) == steps(Side.A, right, left)


def test_the_rival_base_cannot_be_crossed() -> None:
    scenario = mini_race()
    board = scenario.board
    steps = _StepDistances(board)
    rival_base = board.bases[Side.B]
    assert steps(Side.A, Position(0, 0), rival_base) == steps.unreachable
    assert steps(Side.B, Position(0, 1), rival_base) == 4 + 5


def test_a_unit_standing_on_the_dropped_resource_still_needs_two_steps() -> None:
    scenario = mini_race()
    board, state = scenario.board, scenario.initial_state
    on_it = _move(state, "A2", 0, 1)  # nobody carries: A2 just stands there
    beside = _move(state, "A2", 1, 1)  # one step from the resource
    utility = make_utility(board, Side.A, W)
    assert utility(on_it) < utility(beside)


def test_with_equal_progress_weights_the_utility_is_zero_sum() -> None:
    scenario = mini_race()
    board, state = scenario.board, scenario.initial_state
    even = replace(W, rival_progress=W.goal_distance)
    for sample in (state, replace(state, carrier="B1", resource=None), _move(state, "A1", 2, 2)):
        assert make_utility(board, Side.A, even)(sample) == -make_utility(board, Side.B, even)(
            sample
        )


def test_a_win_beats_every_other_state_and_sooner_is_better() -> None:
    scenario = mini_race()
    board, state = scenario.board, scenario.initial_state
    delivered = replace(_move(state, "A1", 0, 0), carrier="A1", resource=None)
    utility = make_utility(board, Side.A, W)
    best_non_terminal = utility(replace(_move(state, "A1", 0, 1), carrier="A1", resource=None))
    assert utility(delivered) > best_non_terminal + W.delivery
    assert make_utility(board, Side.B, W)(delivered) == -utility(delivered)
    late = replace(delivered, turn_number=9)
    assert utility(delivered) > utility(late)


def test_a_draw_is_worth_zero() -> None:
    scenario = mini_race()
    board, state = scenario.board, scenario.initial_state
    assert make_utility(board, Side.A, W)(replace(state, turn_number=board.turn_limit)) == 0.0


def test_blocked_base_entries_cost_two_extra_steps() -> None:
    scenario = mini_race()
    board, state = scenario.board, scenario.initial_state
    # A1 carries at (1,1); entries of base (0,0) are (0,1) and (1,0).
    carrying = replace(_move(state, "A1", 1, 1), carrier="A1", resource=None)
    open_entries = _move(_move(carrying, "A2", 0, 3), "B1", 2, 2)
    blocked = _move(_move(open_entries, "A2", 0, 1), "B1", 1, 0)
    utility = make_utility(board, Side.A, W)
    # +2 steps for A; B1 also gets 1 step closer to the carrier (chase 1 -> 0, gap 2 -> 1)
    expected = 2 * W.goal_distance + W.rival_progress * 1 + W.rival_distance * 1
    assert utility(open_entries) - utility(blocked) == expected


def test_weights_change_the_value() -> None:
    scenario = load_scenario(APENDICE_A)
    board, state = scenario.board, scenario.initial_state
    double = UtilityWeights(
        delivery=20.0, carry=6.0, goal_distance=2.0, rival_distance=1.0, rival_progress=1.0
    )
    base = make_utility(board, Side.A, W)(state)
    assert make_utility(board, Side.A, double)(state) == 2 * base
