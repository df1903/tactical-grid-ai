# TacticalGrid

2D turn-based tactical game on a grid (sides A and B, one resource carried to the own base), used as an environment for BFS, DFS, UCS, A*, Beam Search, Minimax and alpha-beta pruning.

Project 1 of *Sistemas Inteligentes I* (UCALDAS). Team: Jorge Iván Garcia Torres, Daniel Felipe Franco Rincón. Delivery: 2026-10-21.

## Requirements
- [uv](https://docs.astral.sh/uv/) (it provisions Python 3.14)

## Usage
```bash
uv sync                          # install dependencies
uv run python -m tactical_grid scenarios/apendice_a.json --algorithm A_STAR --verify
uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm ALPHA_BETA --depth 3
uv run python -m tactical_grid.gui scenarios/apendice_a.json   # GUI (omit the path to pick a file)
uv run python -m tactical_grid.gui scenarios/prueba_20x20.json   # 20x20 test, 3 units per side
uv run pytest                    # tests
uv run ruff check .              # lint
uv run ruff format --check .     # format check
uv run mypy src                  # types (strict)
```

Options (they override the scenario's `prueba` section): `--mode busqueda|adversarial|partida`,
`--algorithm BFS|DFS|UCS|A_STAR|BEAM|MINIMAX|ALPHA_BETA`, `--heuristic H1|H2`, `--k`, `--depth`,
`--order default|reversed`, `--unit`, `--goal row,col`, `--verify`. The report is printed as JSON.
`--algorithm`, `--heuristic`, `--k`, `--depth` and `--order` take comma-separated lists and run every
applicable combination (a sweep); `--csv PATH` writes one metrics row per run and `--json PATH` the
full reports. Example: `--algorithm MINIMAX,ALPHA_BETA --depth 1,2,3,4 --order default,reversed`.

## Layout
| Path | Content |
|---|---|
| `src/tactical_grid/domain/` | state, actions, successors, costs, game rules |
| `src/tactical_grid/scenario/` | JSON loading and atomic validation |
| `src/tactical_grid/algorithms/` | search, heuristics, Minimax, alpha-beta, utility |
| `src/tactical_grid/gui/` | graphical interface |
| `src/tactical_grid/experiments/` | metrics, verifier, minimal cases |
| `tests/` | automated tests |
| `scenarios/` | JSON scenarios (`apendice_a.json` is the official example) |
| `docs/` | assignment statement (`enunciado.md`), `technical-report.md`, `user-manual.md`, `cases.md` (10 cases, expected vs. obtained), `results/` (raw CSV/JSON of the experiments) |

## Status
All functional requirements are implemented (domain, scenario loader, BFS/DFS/UCS/A*/Beam, Minimax/alpha-beta,
verifier, CLI with sweeps and export, GUI with automatic mode) and documented. Pending: the *Student validation*
field of the method docstrings (cross-review). See `.context/state/current.md`.
