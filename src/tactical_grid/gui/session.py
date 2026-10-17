"""Game session behind the GUI: current state, history and algorithm calls (no tkinter).

The GUI only draws and forwards clicks; every rule and decision comes from `domain`,
`algorithms` and `experiments`.
"""

from dataclasses import dataclass, replace
from typing import Any

from tactical_grid.algorithms.adversarial import ActionOrder, AdversarialResult, alpha_beta, minimax
from tactical_grid.algorithms.utility import UtilityWeights, make_utility
from tactical_grid.domain.model import Action, GameState, Move, Position, Side, Wait
from tactical_grid.domain.rules import apply, is_draw, legal_actions, winner
from tactical_grid.experiments.runner import (
    ADVERSARIAL_ALGORITHMS,
    SEARCH_ALGORITHMS,
    RunError,
    RunOptions,
    canonical,
    run,
)
from tactical_grid.scenario.loader import Scenario

ALGORITHMS = SEARCH_ALGORITHMS + ADVERSARIAL_ALGORITHMS


@dataclass
class Session:
    """A loaded scenario plus the game being played on it."""

    scenario: Scenario
    state: GameState
    history: list[GameState]
    log: list[str]

    @classmethod
    def start(cls, scenario: Scenario) -> Session:
        return cls(scenario, scenario.initial_state, [], [])

    def reset(self) -> None:
        self.state = self.scenario.initial_state
        self.history.clear()
        self.log.clear()

    def undo(self) -> bool:
        if not self.history:
            return False
        self.state = self.history.pop()
        if self.log:
            self.log.pop()
        return True

    def outcome(self) -> str | None:
        """Text for a finished game, or None while it goes on."""
        board = self.scenario.board
        won = winner(board, self.state)
        if won is not None:
            return f"¡Gana el bando {won.value}!"
        if is_draw(board, self.state):
            return "Empate (se alcanzó el límite de turnos)"
        return None

    def play(self, action: Action) -> None:
        if action not in legal_actions(self.scenario.board, self.state):
            raise ValueError(f"illegal action {action!r}")
        mover = self.state.turn
        self.history.append(self.state)
        self.state, cost = apply(self.scenario.board, self.state, action)
        self.log.append(
            f"{self.state.turn_number}. Bando {mover.value}: {_describe(action)} (costo {cost:g})"
        )

    def move_for_click(self, unit_id: str, dest: Position) -> Action | None:
        """The legal move of `unit_id` to `dest`, or None if there is none."""
        for action in legal_actions(self.scenario.board, self.state):
            if isinstance(action, Move) and action.unit_id == unit_id and action.dest == dest:
                return action
        return None

    def destinations(self, unit_id: str) -> list[Position]:
        """Cells the unit can legally move to right now (empty if it is not its side's turn)."""
        return [
            action.dest
            for action in legal_actions(self.scenario.board, self.state)
            if isinstance(action, Move) and action.unit_id == unit_id
        ]

    def wait_for(self, unit_id: str) -> Action | None:
        for action in legal_actions(self.scenario.board, self.state):
            if isinstance(action, Wait) and action.unit_id == unit_id:
                return action
        return None

    def search(self, options: RunOptions) -> dict[str, Any]:
        """Run a single-agent search from the current state; returns the runner report."""
        current = replace(self.scenario, initial_state=self.state)
        return run(current, replace(options, mode="busqueda"))

    def decide(
        self, algorithm: str, depth: int, order: str, record: bool = False
    ) -> AdversarialResult:
        """Minimax or alpha-beta decision for the side to move, from the current state."""
        name = canonical(algorithm)
        if name not in ADVERSARIAL_ALGORITHMS:
            raise RunError(f"adversarial algorithm must be one of {ADVERSARIAL_ALGORITHMS}")
        if order not in ("default", "reversed"):
            raise RunError(f"action order must be default or reversed, got {order!r}")
        if depth < 1:
            raise RunError(f"depth must be at least 1, got {depth}")
        weights = UtilityWeights.from_mapping(self.scenario.utility_weights)
        utility = make_utility(self.scenario.board, self.state.turn, weights)
        algorithm_fn = minimax if name == "MINIMAX" else alpha_beta
        action_order: ActionOrder = "reversed" if order == "reversed" else "default"
        return algorithm_fn(
            self.scenario.board, self.state, depth, utility, action_order, record=record
        )

    def side_to_move(self) -> Side:
        return self.state.turn


def _describe(action: Action) -> str:
    if isinstance(action, Move):
        return f"{action.unit_id} -> ({action.dest.row},{action.dest.col})"
    return f"{action.unit_id} espera"
