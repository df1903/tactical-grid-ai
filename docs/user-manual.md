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

```bash
# graphical interface with the 20x20 test map (three units per side)
uv run python -m tactical_grid.gui scenarios/prueba_20x20.json

# one search from the command line (prints a JSON report)
uv run python -m tactical_grid scenarios/apendice_a.json --algorithm A_STAR --verify
```

## 3. Graphical interface

Open it with `uv run python -m tactical_grid.gui [scenario.json]`. Without a path it asks for a
file. The window is in Spanish.

### 3.1 The map

| Element | How it looks |
|---|---|
| Terrain | color from light green (cheapest) to brown (most expensive); the cost is written in the corner of each cell when the cells are large enough |
| Obstacle | dark grey (not passable) |
| Base | thick outline in the color of its side, with the letter of the side |
| Resource | gold diamond |
| Unit | circle in the color of its side (blue = A, red = B) with its identifier |
| Carrier | gold ring around the unit |
| Selected unit | dashed black ring |
| Search goal | dashed purple circle labeled *meta* |
| Path found | purple line with an arrow |
| Cells the selected unit can move to | green dots |
| Suggested action | green arrow (or the word *esperar*) |

Move the mouse over a cell to see its row, column, terrain, cost and any unit or resource on it.
The legend under the map explains the colors.

### 3.2 Panel (right side)

- **Partida:** a colored banner says whose turn it is (or who won); below it, the move number
  against the turn limit, the carrier of the resource, the selected unit and the search goal.
- **Clic izquierdo sobre el mapa:** choose what a left click does.
  - *Seleccionar / mover unidades:* click a unit to select it; click a green dot to move it.
  - *Fijar meta de la búsqueda:* click the goal cell for a search (a right click always sets
    the goal, in any mode).
- **Buttons:** *Esperar* (selected unit waits), *Deshacer* (undo the last move), *Reiniciar
  partida*, *Abrir escenario...*. An invalid JSON is rejected with a list of every error and
  the current game stays untouched.
- **Algoritmo:** choose BFS, DFS, UCS, A\*, Beam Search, Minimax or Alfa-beta. Only the
  options that apply appear: heuristic (A\*, Beam), width *k* (Beam), depth and action order
  (Minimax, alpha-beta). *Verificar resultado* runs the six checks (RF-42).
- **▶ Ejecutar:** runs the algorithm on the **current** state.
  - Searches (BFS … Beam): from the selected unit to the goal; the path is drawn and the
    metrics appear in the *Resultados* tab.
  - Minimax / alpha-beta: the best action for the side to move is drawn in green and the
    values of every root action are listed. *Aplicar jugada sugerida* plays it.
- **Jugar turno con la IA:** the side to move plays the decision of the chosen algorithm
  (alpha-beta if a search algorithm is selected).
- **Pestañas:** *Resultados* (metrics and report) and *Jugadas* (numbered history).

### 3.3 Three typical uses

1. **Play by hand.** Select a unit of the side that has the turn, click a green dot. The
   other side answers by hand or with *Jugar turno con la IA*. The game ends when a carrier
   reaches its own base (winner) or the turn limit is reached (draw).
2. **Watch a path search.** Select `A1`, switch to *Fijar meta* and click a cell, pick an
   algorithm and press *Ejecutar*. Change the heuristic or *k* and run again to compare.
3. **Automatic game.** In *Modo automático (IA contra IA)* pick Minimax or Alfa-beta, the
   depth and order, set the pause between moves with the slider (0–2000 ms) and press
   *▶ Iniciar partida automática*. Both sides play with the chosen algorithm until someone
   wins or the turn limit is reached. The button becomes *⏸ Pausar*; *Deshacer*, *Reiniciar*
   and *Abrir escenario* also stop it. While it is paused you may take over by hand.

## 4. Command line

```bash
uv run python -m tactical_grid <scenario.json> [options]
```

Options override the `prueba` section of the JSON:

| Option | Meaning |
|---|---|
| `--mode` | `busqueda`, `adversarial` or `partida` (describes the loaded game) |
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
`tiempo_segundos` (adversarial). Errors in the scenario or in the options go to the standard
error stream with exit code 2.

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
| `utilidad` | weights `entrega`, `recurso_cargado`, `distancia_objetivo`, `distancia_rival` | 10 / 3 / 1 / 0.5 |
| `prueba.algoritmo` | algorithm of the test | none |
| `prueba.heuristica` | `H1` or `H2` | `H1` |
| `prueba.k` | beam width | none |
| `prueba.orden_acciones` | `default` or `reversed` | `default` |

Scenarios included in `scenarios/`:

| File | Use |
|---|---|
| `apendice_a.json` | official 4×4 example |
| `caso_01` … `caso_05` | cases 1–5 (searches) |
| `caso_07_decision_adversarial.json` | cases 6–10 |
| `prueba_15x15.json` | 15×15 performance test (three units per side) |
| `prueba_20x20.json` | 20×20 test (three units per side); open it in the GUI |

To try another map, copy a file, change dimensions, costs, positions or units, and open it; no
code change is needed.

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
```

(Minimax at depth 6 on the 15×15 map takes about 16 s.) The expected values of the 10 cases are
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
