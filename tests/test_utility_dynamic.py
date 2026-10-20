import pytest

from helpers import SCENARIOS
from tactical_grid.algorithms.adversarial_dynamic import alpha_beta_dynamic
from tactical_grid.algorithms.utility import UtilityWeights, make_utility
from tactical_grid.algorithms.utility_dynamic import make_dynamic_utility
from tactical_grid.domain.dynamic import apply, initial_dynamic_state
from tactical_grid.domain.model import Move, Position
from tactical_grid.scenario.loader import DEFAULT_UTILITY_WEIGHTS, load_scenario
from test_dynamic_rules import RULES, Unit, make

WEIGHTS = UtilityWeights.from_mapping(DEFAULT_UTILITY_WEIGHTS)
UNITS: list[Unit] = [("A1", "A", 2, 2), ("A2", "A", 3, 0), ("B1", "B", 4, 3), ("B2", "B", 0, 4)]


def test_it_equals_the_base_utility_on_a_cost_one_map() -> None:
    board, state = make(UNITS, resource=(0, 3))
    base = make_utility(board, state.turn, WEIGHTS)
    dynamic = make_dynamic_utility(board, state.turn, WEIGHTS)
    assert dynamic(state) == base(state.base)
    moved = apply(board, state, Move("A1", Position(1, 2)), RULES)
    assert dynamic(moved) == base(moved.base)


def test_entering_expensive_terrain_counts_its_turns() -> None:
    cheap, state = make(UNITS, resource=(0, 3))
    costly, state_costly = make(UNITS, resource=(0, 3), special={(1, 2): "bosque"})
    to_cheap = make_dynamic_utility(cheap, state.turn, WEIGHTS)
    to_costly = make_dynamic_utility(costly, state.turn, WEIGHTS)
    # el camino por el bosque (costo 4) o el rodeo: nunca vale lo mismo que con camino
    assert to_costly(state_costly) <= to_cheap(state)


def test_the_remaining_recovery_of_the_closest_unit_lowers_the_value() -> None:
    board, state = make(UNITS, resource=(0, 3))
    utility = make_dynamic_utility(board, state.turn, WEIGHTS)
    stuck = apply(board, state, Move("A1", Position(1, 2)), RULES)
    free = stuck.__class__(base=stuck.base, recovery=tuple((u, 0) for u, _ in stuck.recovery))
    free_value = utility(free)
    waiting = stuck.__class__(
        base=stuck.base, recovery=tuple((u, 3 if u == "A1" else 0) for u, _ in stuck.recovery)
    )
    # el valor se mide desde A (MAX): esperar 3 turnos más lo empeora
    assert utility(waiting) < free_value


def test_advancing_now_is_better_than_postponing_it() -> None:
    # A1 y A2 podrían avanzar hacia el recurso entrando a un bosque (costo 4 -> 3 turnos de espera)
    units: list[Unit] = [("A1", "A", 2, 2), ("A2", "A", 4, 0), ("B1", "B", 4, 3), ("B2", "B", 0, 4)]
    special = {(1, 2): "bosque", (2, 1): "bosque", (2, 3): "bosque", (3, 2): "bosque"}
    board, state = make(units, resource=(0, 2), special=special)
    utility = make_dynamic_utility(board, state.turn, WEIGHTS)
    result = alpha_beta_dynamic(board, state, 4, utility, RULES)
    assert result.action is not None
    # no se queda procrastinando: la acción elegida acerca a la unidad más cercana al recurso
    assert getattr(result.action, "unit_id", "") != "A2"


def test_the_30x30_game_makes_progress_and_does_not_oscillate() -> None:
    scenario = load_scenario(SCENARIOS / "escenario_30x30.json")
    board = scenario.board
    utility = make_dynamic_utility(board, scenario.initial_state.turn, WEIGHTS)
    state = initial_dynamic_state(scenario.initial_state)
    seen: list[tuple[str, Position]] = []
    for _ in range(12):
        result = alpha_beta_dynamic(board, state, 4, utility, scenario.dynamic_rules)
        assert result.action is not None
        if isinstance(result.action, Move) and state.turn.value == "A":
            seen.append((result.action.unit_id, result.action.dest))
        state = apply(board, state, result.action, scenario.dynamic_rules)
        utility = make_dynamic_utility(board, state.turn, WEIGHTS)
    # ninguna celda se repite en las seis jugadas de A: avanza en lugar de ir y venir
    assert len({dest for _, dest in seen}) == len(seen)


@pytest.mark.parametrize("weight", ["delivery", "carry", "goal_distance", "rival_progress"])
def test_the_weights_change_the_value(weight: str) -> None:
    board, state = make(UNITS, resource=(0, 3), carrier="A1")
    values = dict(DEFAULT_UTILITY_WEIGHTS)
    other = make_dynamic_utility(board, state.turn, UtilityWeights.from_mapping(values))(state)
    values[weight] = values[weight] + 7
    changed = make_dynamic_utility(board, state.turn, UtilityWeights.from_mapping(values))(state)
    if weight == "delivery":
        assert changed == other  # solo pesa en estados terminales
    else:
        assert changed != other
