# TacticalGrid

2D turn-based tactical game on a grid (sides A and B, one resource carried to the own base), used as an environment for BFS, DFS, UCS, A*, Beam Search, Minimax and alpha-beta pruning.

Project 1 of *Sistemas Inteligentes I* (UCALDAS). Team: Jorge Iván Garcia Torres, Daniel Felipe Franco Rincón. Delivery: 2026-10-21.

## Requirements
- [uv](https://docs.astral.sh/uv/) (it provisions Python 3.14)

## Run (default)
```bash
uv sync                                  # once: install dependencies
uv run python -m tactical_grid.gui       # open the window
```
The window opens empty: press **Seleccionar JSON** (pick any file of `scenarios/`), choose the
**Algoritmo** (BFS, DFS, UCS, A*, Beam, Minimax, Alfa-beta), adjust its parameters if you want and
press **Ejecutar**, **Animar** or **Aplicar jugada**. Everything else below is optional.

## Usage
```bash
uv sync                          # install dependencies
uv run python -m tactical_grid scenarios/apendice_a.json --algorithm A_STAR --verify
uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm ALPHA_BETA --depth 3
uv run python -m tactical_grid.gui scenarios/caso_07_decision_adversarial.json   # GUI (omit the path to pick a file)
uv run python -m tactical_grid.gui scenarios/prueba_20x20.json   # 20x20 test, 3 units per side
uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --mode partida --play humano --depth 3   # you vs the AI
uv run python -m tactical_grid scenarios/caso_11_dinamico.json --algorithm ALPHA_BETA --depth 3 --verify   # dynamic variant
uv run pytest                    # tests
uv run ruff check .              # lint
uv run ruff format --check .     # format check
uv run mypy src                  # types (strict)
```

Options (they override the scenario's `prueba` section): `--mode busqueda|adversarial|partida`,
`--algorithm BFS|DFS|UCS|A_STAR|BEAM|MINIMAX|ALPHA_BETA`, `--heuristic H1|H2`, `--k`, `--depth`,
`--order default|reversed`, `--unit`, `--goal row,col`, `--verify`. The report is printed as JSON.
With `--mode partida`, `--play auto` plays a whole game AI vs AI and `--play humano [--side A|B]` lets you
play against the AI by typing the number of a legal move (`q` quits); without `--play` it only describes the game.
`--variant base|dinamica` (or `juego.variante` in the JSON) selects the rules of the adversarial game: the optional
dynamic variant turns terrain cost into waiting turns and makes the tackle steal the resource (user manual, section 5.1).
In the GUI the **Juegas** selector chooses your side against the AI and **Partida automática** lets the AI play both sides.
`--algorithm`, `--heuristic`, `--k`, `--depth` and `--order` take comma-separated lists and run every
applicable combination (a sweep); `--csv PATH` writes one metrics row per run and `--json PATH` the
full reports. Example: `--algorithm MINIMAX,ALPHA_BETA --depth 1,2,3,4 --order default,reversed`.

## Layout
| Path | Content |
|---|---|
| `src/tactical_grid/domain/` | state, actions, successors, costs, game rules (`rules.py`; optional dynamic variant in `dynamic.py`) |
| `src/tactical_grid/scenario/` | JSON loading and atomic validation |
| `src/tactical_grid/algorithms/` | search, heuristics, Minimax, alpha-beta, utility |
| `src/tactical_grid/gui/` | graphical interface (`app.py`, tkinter) |
| `src/tactical_grid/experiments/` | runner, sweeps, verifier, full games from the terminal (`game.py`) |
| `tests/` | automated tests |
| `scenarios/` | JSON scenarios (`apendice_a.json` is the official example) |
| `docs/` | assignment statement (`enunciado.md`), `technical-report.md`, `user-manual.md`, `cases.md` (10 cases, expected vs. obtained), `results/` (raw CSV/JSON of the experiments), `latex/` (LaTeX sources of the two manuals, build with `make` there), `pdf/` (`Manual_Tecnico.pdf`, `Manual_de_Usuario.pdf`) |

## Status
All functional requirements are implemented (domain with move and tackle actions, scenario loader, BFS/DFS/UCS/A*/Beam,
Minimax/alpha-beta with a moves-to-win utility, verifier, CLI with sweeps and export, one GUI with per-algorithm parameter
panels, manual and automatic play; whole games from the terminal, person vs AI or AI vs AI; optional dynamic rules variant
with its own utility, Minimax and alpha-beta) and documented. All scenarios live in `scenarios/`; the raw results of the experiments
are in `docs/results/`. See `docs/user-manual.md` to reproduce them and `.context/state/current.md` for the project state.
