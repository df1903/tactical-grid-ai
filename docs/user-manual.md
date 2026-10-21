# TacticalGrid — User Manual

How to install, run and use TacticalGrid. For design and results see
[`technical-report.md`](technical-report.md); for the 10 demonstration cases see
[`cases.md`](cases.md).

## 1. Requirements and installation

- Windows with [`uv`](https://docs.astral.sh/uv/) installed (it provisions Python 3.14).
- `tkinter` ships with Python on Windows; nothing else is needed for the interface.

```bash
git clone <repository-url>
cd tactical-grid-ai
uv sync          # creates the virtual environment from uv.lock
uv run pytest    # optional: check the installation (all tests should pass)
```

## 2. Quick start

Default way to run it: `uv run python -m tactical_grid.gui`. The window opens empty; press
*Seleccionar JSON*, pick a file of `scenarios/`, choose the algorithm and press *Ejecutar*.

```bash
# default: open the window and choose the scenario and the algorithm there
uv run python -m tactical_grid.gui

# graphical interface already loaded with the 20x20 test map (three units per side)
uv run python -m tactical_grid.gui scenarios/prueba_20x20.json

# one search from the command line (prints a JSON report)
uv run python -m tactical_grid scenarios/apendice_a.json --algorithm A_STAR --verify
```

## 3. Graphical interface

Open it with `uv run python -m tactical_grid.gui [scenario.json]`. Without a path, use *Seleccionar
JSON*. The window is in Spanish and has the same layout for every algorithm.

### 3.1 The map

| Element | How it looks |
|---|---|
| Terrain | color from light green (cheapest) to brown (most expensive) |
| Obstacle | dark grey (not passable) |
| Base | thick outline in the color of its side |
| Resource | gold diamond (Minimax / alpha-beta games) |
| Unit | circle in the color of its side (blue = A, red = B) with its identifier |
| Carrier | gold ring around the unit |
| Cells expanded by a search | orange, in expansion order when animated |
| Search goal | green outline |
| Path found | purple line |
| Last move or decision | purple arrow (from the unit to the cell, or to the carrier it tackles) |
| Selected unit | green outline; its legal destinations are green dots |

### 3.2 Layout

- **Top bar:** *Seleccionar JSON* (the file is validated; an invalid one shows every error and
  nothing changes) and the **Algoritmo** selector: BFS, DFS, UCS, A\*, Beam, Minimax, Alfa-beta.
- **Estado:** turn, move number against the limit, carrier of the resource and the color legend.
- **Parámetros:** changes with the algorithm. DFS: neighbor order. A\*: heuristic (h1 Manhattan,
  h2 obstacle-aware). Beam: heuristic and width *k*. Minimax / alpha-beta: depth, action order
  and the five utility weights. The initial values come from the scenario (`prueba`, `utilidad`).
- **Métricas:** result of the last run (and the verification when enabled).
- **Traza:** expansion order of a search, or the values of every root action of a decision
  (`*` marks the chosen one) followed by the game history.
- **Bottom bar:** *Ejecutar*, *Animar*, *Aplicar jugada*, *Reiniciar*, *Verificar (RF-42)*, the
  *Juegas* selector (your side), *Partida automática* and the animation speed.

### 3.3 Using it

- **Searches (BFS … Beam):** *Ejecutar* shows the path and the metrics; *Animar* replays the
  expansion cell by cell. The unit and the goal come from `prueba` of the scenario.
- **Minimax / alpha-beta:** *Ejecutar* shows the best action for the side to move without
  playing it. *Aplicar jugada* plays it and, after a short pause, the rival answers with the same
  algorithm and parameters. The game ends with a delivery or at the turn limit.
- **Playing by hand:** with Minimax or alpha-beta selected, click a unit of the side to move and
  then one of the green dots; to tackle, click the rival carrier when one of your units is next
  to it. The rival answers automatically.
- **Dynamic variant:** *Minimax dinámico* and *Alfa-beta dinámico* play with the rules of
  section 5.1. They are preselected when the scenario declares `"variante": "dinamica"`
  (for example `caso_11_dinamico.json`). The *Estado* panel then lists the units that are still
  recovering (own turns left) and the immunity of the carrier; everything else (clicks, *Juegas*,
  *Partida automática*, *Verificar*) works as with the base algorithms.
- **Your side (*Juegas*):** by default you play the side that opens the game. Pick *Bando A* or
  *Bando B* to choose; if you play the side that does not move first, the AI opens. Changing it
  restarts the game, and the *Estado* panel shows which side you play.
- **Partida automática:** the AI plays both sides until the end (same rules, algorithm and
  parameters for both). Press it again (*Pausar*) to stop without losing the game; *Reiniciar*
  also stops it.
- **Verificar (RF-42):** for searches, runs checks 1–5 (legal moves, obstacles, cost, goal and
  valid states); for Minimax/alpha-beta, runs check 6 (legal considered and selected actions).
  In a game, the applicable adversarial check is run for each decision and listed in *Métricas*.
- **Reiniciar:** returns to the initial state of the scenario; changing the algorithm also
  restarts the game.

## 4. Command line

```bash
uv run python -m tactical_grid <scenario.json> [options]
```

Options override the `prueba` section of the JSON:

| Option | Meaning |
|---|---|
| `--mode` | `busqueda`, `adversarial` or `partida` (describes the loaded game, or plays it with `--play`) |
| `--play` | with `partida`: `auto` (AI vs AI, whole game) or `humano` (you vs the AI, pick a move by its number, `q` quits) |
| `--side` | with `--play humano`: your side, `A` (default) or `B`; the AI uses `--algorithm`, `--depth`, `--order`, `--variant` |
| `--variant` | adversarial rules: `base` or `dinamica` (section 5.1); default `juego.variante` of the scenario |
| `--algorithm` | `BFS`, `DFS`, `UCS`, `A_STAR` (`A*`, `A_ESTRELLA`), `BEAM`, `MINIMAX`, `ALPHA_BETA` |
| `--heuristic` | `H1` (Manhattan) or `H2` (obstacle aware); default `H1` |
| `--k` | beam width |
| `--depth` | Minimax / alpha-beta depth (default: `juego.profundidad_maxima_minimax`) |
| `--order` | `default` or `reversed` action order |
| `--unit`, `--goal row,col` | start unit and goal of a search |
| `--verify` | run the checks of RF-42; the report gets a `verificacion` section |
| `--csv PATH` | write one metrics row per run |
| `--json PATH` | write the full reports (path, root values, checks) |

`--algorithm`, `--heuristic`, `--k`, `--depth` and `--order` accept comma-separated lists and
run every combination that applies (a *sweep*), for example:

```bash
uv run python -m tactical_grid scenarios/caso_05_beam_k.json --algorithm BEAM --k 1,2,4,8 --csv beam.csv
uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json \
    --algorithm MINIMAX,ALPHA_BETA --depth 1,2,3,4 --order default,reversed --verify
```

The report is a JSON object with keys equivalent to Appendix B of the assignment:
`algoritmo`, `exito`, `camino`, `costo`, `longitud`, `estados_generados`, `estados_expandidos`,
`maximo_frontera`, `tiempo_segundos` (searches) and `profundidad`, `accion`, `valor`,
`nodos_generados`, `nodos_evaluados`, `nodos_podados`, `profundidad_alcanzada`, `valores_raiz`,
`tiempo_segundos` (adversarial). With the dynamic variant the adversarial report also has
`"variante": "dinamica"`. Errors in the scenario or in the options go to the standard error
stream with exit code 2.

### 4.1 Playing a whole game from the terminal (`--mode partida`)

Without `--play` the mode only prints a summary of the loaded game. With `--play` it plays the
scenario to the end, from the initial state, with Minimax or alpha-beta on the AI side:

```bash
# AI against AI: prints the whole game as JSON
uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json \
    --mode partida --play auto --algorithm ALPHA_BETA --depth 3
# you against the AI (you are side A; add --side B to play second)
uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json \
    --mode partida --play humano --depth 3
# the same with the dynamic variant
uv run python -m tactical_grid scenarios/caso_11_dinamico.json --mode partida --play humano --depth 3
```

- **Both sides play under the same rules** and the AI uses the same algorithm, depth, action
  order and weights whichever side it plays; MAX and MIN are only the roles inside each
  decision's tree. `--algorithm` defaults to the scenario's adversarial algorithm or alpha-beta;
  the depth comes from `--depth` or `juego.profundidad_maxima_minimax`.
- **`--play humano`:** on your turn the map is drawn as text (terrain initial, units, `*` for
  the carrier, `$` for the resource, `<A>`/`<B>` for the bases) and your legal actions are listed
  with a number. Type the number and press Enter; `q` (or closing the input) abandons the game.
  An invalid answer is asked again. After each of your moves the AI answers and its move is
  printed. A side with no legal action passes its turn.
- **Report** (printed when the game ends): `modo`, `variante`, `algoritmo`, `profundidad`,
  `orden`, `jugadores` (who plays each side), `terminada`, `abandonada`, `ganador` (`A`, `B` or
  `null` for a draw or an abandoned game), `turnos_jugados`, `jugadas` (turn, side, player,
  action, and for the AI its value and generated nodes) and `estado_final`.
- `--depth` accepts a list here too (one game per value); `--play` only applies to `partida`
  and `--side` only to `--play humano`.

## 5. Scenario file (JSON)

The format is the one of Appendix A of the assignment:

```json
{
  "version": "1.0",
  "mapa": {"filas": 4, "columnas": 4},
  "tipos_terreno": {"camino": {"costo": 1, "transitable": true}, "muro": {"transitable": false}},
  "terreno": [["camino", "camino"], ["muro", "camino"]],
  "bases": {"A": {"fila": 0, "columna": 0}, "B": {"fila": 3, "columna": 3}},
  "recurso": {"fila": 2, "columna": 2},
  "unidades": [{"id": "A1", "bando": "A", "tipo": "estandar", "fila": 0, "columna": 1}],
  "turno": "A",
  "juego": {"portador_recurso": null, "profundidad_maxima_minimax": 4},
  "prueba": {"modo": "busqueda", "unidad_inicio": "A1", "objetivo": {"fila": 3, "columna": 2}}
}
```

Terrain names are free (read from `tipos_terreno`); non-passable terrains need no `costo`;
costs may be decimals; sides `A`/`a` are accepted. The file is rejected as a whole, with a
list of every error, when any of the nine validations fails (dimensions, unknown terrain,
cost not positive, element outside the map, unit on an obstacle, repeated unit id, invalid
side, invalid turn, carrier that does not exist) or when two units share a cell.

Optional fields of the team (they never replace the mandatory ones):

| Field | Meaning | Default |
|---|---|---|
| `juego.limite_turnos` | turn limit; the game is a draw when reached | 100 |
| `utilidad` | weights `entrega`, `recurso_cargado`, `distancia_objetivo`, `distancia_rival`, `progreso_rival` | 10 / 3 / 1 / 0.5 / 0.5 |
| `prueba.algoritmo` | algorithm of the test | none |
| `prueba.heuristica` | `H1` or `H2` | `H1` |
| `prueba.k` | beam width | none |
| `prueba.orden_acciones` | `default` or `reversed` | `default` |
| `juego.variante` | rules of the adversarial game: `base` or `dinamica` (section 5.1) | `base` |
| `juego.penalizacion_placaje` | dynamic variant: own turns the victim of a steal cannot act | 2 |
| `juego.inmunidad_robo` | dynamic variant: rival turns the new carrier cannot be tackled | 1 |

Scenarios included in `scenarios/`:

| File | Use |
|---|---|
| `apendice_a.json` | official 4×4 example |
| `caso_01` … `caso_05` | cases 1–5 (searches) |
| `caso_07_decision_adversarial.json` | cases 7–10 (20×20, three units per side) |
| `caso_11_dinamico.json` | the same map and units as `caso_07`, declared as `"variante": "dinamica"` (penalty 2, immunity 1) |
| `prueba_15x15.json` | 15×15 performance test (three units per side) |
| `prueba_20x20.json` | 20×20 test (three units per side); open it in the GUI |
| `escenario_03x03.json` … `escenario_30x30.json` | the same game at six sizes, for the size experiments (the 30×30 one has a limit of 200 turns) |

To try another map, copy a file, change dimensions, costs, positions or units, and open it; no
code change is needed.

### 5.1 Dynamic variant (optional)

An alternative set of rules for the adversarial game, selected with `juego.variante: "dinamica"`
or `--variant dinamica`. The base rules are not modified and a scenario without the field keeps
playing as before. The variant changes two things:

- **Terrain cost becomes waiting time.** A unit that enters a cell of cost `c` cannot act for
  `ceil(c) - 1` of its side's next turns (cost 1: no wait; cost 3: two turns; cost 7: six turns).
  While waiting, the unit neither moves nor tackles, but it can be tackled. The counters of a
  side go down by one at the end of each of its turns.
- **The tackle steals.** A free unit adjacent to the rival carrier takes the resource: it becomes
  the carrier, nobody moves and the resource never lies on the ground. The victim waits
  `penalizacion_placaje` own turns (the maximum with what it already had, not the sum) and the
  new carrier cannot be tackled for `inmunidad_robo` rival turns. Stealing on the own base wins
  at once.

Everything else (four directions, one unit per cell, the rival base forbidden, pickup on
arrival, delivery, turn limit, passing when blocked) is as in the base game. The AI uses its own
utility, measured in own turns instead of steps, with the same weights from the `utilidad`
section. Details and measurements: technical report, sections 3.1 and 10.6.

## 6. Reproducing the reported experiments

Run from the repository root. Each command regenerates a file of `docs/results/`; counts and
costs are identical on every run, times vary.

```bash
R=docs/results; U="uv run python -m tactical_grid"
$U scenarios/caso_01_bfs_vs_dfs.json --algorithm BFS,DFS,UCS --verify --csv $R/caso_01_bfs_vs_dfs.csv --json $R/caso_01_bfs_vs_dfs.json
$U scenarios/caso_02_bfs_vs_ucs.json --algorithm BFS,DFS,UCS --verify --csv $R/caso_02_bfs_vs_ucs.csv --json $R/caso_02_bfs_vs_ucs.json
$U scenarios/caso_03_obstaculo_heuristica.json --algorithm UCS,A_STAR --heuristic H1,H2 --verify --csv $R/caso_03_obstaculo_heuristica.csv --json $R/caso_03_obstaculo_heuristica.json
$U scenarios/caso_04_comparacion_heuristicas.json --algorithm UCS,A_STAR --heuristic H1,H2 --verify --csv $R/caso_04_comparacion_heuristicas.csv --json $R/caso_04_comparacion_heuristicas.json
$U scenarios/caso_05_beam_k.json --algorithm UCS,BEAM --heuristic H1 --k 1,2,4,8 --verify --csv $R/caso_05_beam_k.csv --json $R/caso_05_beam_k.json
$U scenarios/caso_07_decision_adversarial.json --algorithm MINIMAX,ALPHA_BETA --depth 1,2,3,4,5 --order default,reversed --verify --csv $R/casos_07_10_adversarial.csv --json $R/casos_07_10_adversarial.json
$U scenarios/prueba_20x20.json --algorithm ALPHA_BETA --depth 2,3,4,5,6 --csv $R/rendimiento_20x20.csv
$U scenarios/prueba_15x15.json --algorithm ALPHA_BETA --depth 5,6,7 --csv $R/rendimiento_15x15.csv
$U scenarios/prueba_15x15.json --algorithm MINIMAX --depth 4,5,6 --csv $R/rendimiento_15x15_minimax.csv
$U scenarios/apendice_a.json --algorithm BFS,DFS,UCS,A_STAR,BEAM --heuristic H1,H2 --k 1,2,4,8 --verify --csv $R/apendice_a.csv
$U scenarios/caso_11_dinamico.json --algorithm MINIMAX,ALPHA_BETA --depth 1,2,3,4 --verify --csv $R/caso_11_dinamico.csv --json $R/caso_11_dinamico.json
```

(Minimax at depth 6 on the 15×15 map takes about 10 s.) The expected values of the 10 cases are
asserted by the tests: `uv run pytest tests/test_cases_f2.py tests/test_cases_f3.py
tests/test_case_6.py tests/test_cases_f4.py`.

## 7. Tests and quality checks

```bash
uv run pytest                 # all tests
uv run ruff check .           # lint
uv run ruff format --check .  # formatting
uv run mypy src               # strict type checking
```

The window tests need a display; they are skipped automatically when tkinter cannot open one.

## 8. Troubleshooting

| Problem | Cause and solution |
|---|---|
| `Invalid scenario` / exit code 2 | the JSON failed validation; the message lists every error |
| "El algoritmo no encontró camino" | the goal is unreachable, or Beam with a small `k` pruned the only way; increase `k` |
| Minimax is slow | lower the depth or use alpha-beta; see technical report 10.5 for measured times |
| The window does not open | check that Python has `tkinter` (`uv run python -c "import tkinter"`) |
