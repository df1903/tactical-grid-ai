# TacticalGrid — Technical Report

Project 1 of *Sistemas Inteligentes I* (Universidad de Caldas).
Team: Jorge Iván Garcia Torres, Daniel Felipe Franco Rincón (team of two, G15).
Delivery and defense: 2026-10-21. Repository version: see the Git tag named in section 15.

Companion documents: [`user-manual.md`](user-manual.md) (installation and use),
[`cases.md`](cases.md) (the 10 minimum cases, expected vs. obtained), and the raw experiment
output in [`results/`](results/).

---

## 1. Summary

TacticalGrid is a deterministic, turn-based 2D game on a grid. Sides **A** and **B** each own
a base and some units; one resource lies on the map; the first side to carry the resource to
its own base wins. The game is the environment for BFS, DFS, UCS, A\*, Beam Search, Minimax and
alpha-beta pruning.

Everything the assignment lists as mandatory is implemented: composite state, the seven
algorithms with their metrics, two admissible heuristics, a utility function, atomic scenario
loading with the nine validations, the six-check verifier, a CLI with sweeps and CSV/JSON
export, a minimal GUI with an automatic mode, and the ten demonstration cases. The project has
170+ automated tests; `ruff` and `mypy --strict` pass.

What is **not** done at the time of writing: the *Student validation* field of the method
docstrings (cross-review by the other team member) and the optional RF-41 view of explored
states. Both are listed in section 13.

## 2. Problem modeling and state representation

### 2.1 Static data (`Board`) and dynamic data (`GameState`)

| Part | Content | Changes during a game? |
|---|---|---|
| `Board` | rows, columns, terrain grid, terrain catalog (cost, passable), base of each side, side of each unit, turn limit | no |
| `GameState` | position of every unit, carrier of the resource (or the resource cell if nobody carries it), side to move, turn number | yes (frozen dataclass) |

`GameState` is immutable and hashable, so it can be a key in visited sets and frontiers.
`Board` is separate because it never changes: successors reuse it and states stay small.

### 2.2 Why this representation is sufficient (RF-13)

A decision in this game depends on four things, and the state holds each of them:

1. **Where every unit is** (`positions`): needed to know which cells are free (one unit per
   cell), who is adjacent to the carrier (interception) and how far each unit is from its
   objective.
2. **Whose unit each one is**: held in `Board.unit_sides`; units never change side, so it is
   static.
3. **Who has the resource, or where it lies** (`carrier` / `resource`): decides what a move
   can achieve. The same move into the base wins when the unit carries the resource and does
   nothing otherwise. Exactly one of the two fields is set.
4. **Whose turn it is** (`turn`, plus `turn_number` for the turn limit): decides which units
   have legal actions and who is MAX or MIN in the tree.

Nothing else influences the rules (there is no health, ammunition or hidden information), so
two situations with equal `positions`, `carrier`/`resource`, `turn` and `turn_number` have
exactly the same legal actions, successors, costs and outcome. Conversely, dropping any of the
four fields would merge situations whose futures differ. A state keyed only by (row, column)
fails RF-10 and RF-11; case 6 demonstrates it (see [`cases.md`](cases.md)).

For the single-unit searches (BFS to A\*, RF-14) the adversary is ignored, so the search
state is projected to the position of the moving unit (section 6.1). The full composite state
is used by the game and by Minimax / alpha-beta.

### 2.3 Unambiguous identification (RF-12)

| Element | Where |
|---|---|
| Initial state | `Scenario.initial_state`, built by `scenario/loader.py` from the JSON |
| Valid actions | `domain.rules.legal_actions(board, state)` |
| Successors | `domain.rules.successors(board, state)` → `(action, next state, cost)` |
| Goal condition | single-unit search: unit on the goal cell; game: `domain.rules.winner` |
| Action cost | `domain.rules.apply` (terrain cost of the destination cell) |

## 3. Game rules (RF-09)

All rules are deterministic and symmetric: MAX and MIN are roles of the search tree, not
different agents (RF-07, RF-28). MIN is not at a disadvantage: minimizing MAX's utility *is*
playing for its own side.

- **Movement:** four directions (up, down, left, right).
- **Cost:** paid on *entering* the destination cell; the start cell costs nothing. Costs and
  passability come from the `tipos_terreno` catalog of the JSON, never from the code.
- **Occupation:** one unit per cell. Bases and the resource cell may be stepped on when free;
  the **rival base cannot** be entered.
- **Turns:** the side to move chooses one of its units and moves one of its units
  to a neighboring cell. There is no *wait* action: moving one unit leaves the others in place.
- **Pickup:** a unit picks the resource up when it *arrives* at its cell (a unit that stays
  put does not pick it up again).
- **Delivery:** the side whose carrier reaches its own base wins. Delivery beats interception
  in the same move.
- **Interception (loss of the carrier):** after *any* move that leaves a rival adjacent to the
  carrier, the resource drops on the carrier's cell (no transfer to the rival, so no
  tie-break). The original carrier cannot pick it up again while it stays on that cell; any
  other unit picks it up on arrival.
- **End of game:** victory on delivery; draw when `turn_number` reaches the turn limit
  (`juego.limite_turnos`, default 100). A finished game has no legal actions. A side with no
  legal move (all its units blocked) passes its turn; the pass is not an action, and Minimax
  evaluates such a node as a leaf.

Order of resolution inside a move: (1) pickup, (2) delivery check, (3) interception.

## 4. Costs

- `g(n)` is the sum of destination-cell costs along the path; the start cell is free.
- Costs may be integers or decimals (G12): any positive number is accepted.
- A\* heuristics are scaled by the **cheapest passable terrain cost of the loaded scenario**
  (`heuristics.min_step_cost`). A JSON with costs below 1 therefore does not break
  admissibility (assignment section 18.4).
- No terrain name, cost, dimension or position is written in `domain/` or `algorithms/`
  (RF-03, RF-37, RNF-03, RNF-04).

## 5. Architecture

Five components, as decided on 2026-10-07 (RNF-05); no database or network.

| Component | Responsibility | Depends on |
|---|---|---|
| `domain` | state, actions, legal actions, successors, costs, winner / draw | nothing |
| `scenario` | JSON loading, nine validations, translation to `domain` objects | `domain` |
| `algorithms` | BFS, DFS, UCS, A\*, Beam, Minimax, alpha-beta, heuristics, utility | `domain` |
| `experiments` | runner (modes), sweeps, CSV/JSON export, verifier | `algorithms`, `scenario` |
| `gui` | tkinter window and `Session` (game state behind the window) | all of the above |

`algorithms` never reads JSON and never knows the GUI. The GUI holds no game rule: it calls
`domain` (legal moves, `apply`), `algorithms` (decisions) and `experiments.runner` (searches).
`gui/session.py` is free of tkinter so it can be tested without a display.

JSON keys are Spanish (the assignment's contract) and are read only in `scenario/`; the code
uses English names.

## 6. Algorithms

### 6.1 Model of the single-unit searches (RF-14)

The assignment asks BFS, DFS, UCS, A\* and Beam to find a path for one unit, ignoring the
adversary. Treating rival units as fixed obstacles would leave the official example
(Appendix A) without a solution, because B1 stands on the goal cell. The decision (2026-10-14)
is therefore:

- rival units are removed from the search problem (the rival base still cannot be entered);
- only the start unit moves; its teammates stay put and block their cells;
- the turn does not alternate and the resource is ignored;
- the search state is therefore equivalent to the unit's position, and successors and costs
  still come from `domain.successors`, so the verifier checks the real rules.

### 6.2 Common conventions (G7, G8)

| Convention | Value |
|---|---|
| Search type | graph search; a state is never generated twice (skipped if it is in the frontier or already expanded) |
| Goal test | when the node is *expanded* (needed for UCS / A\* optimality; same for all for comparability) |
| Initial state | counts as generated |
| Successor order | up, down, left, right |
| Tie-break | the node that entered the frontier first is expanded first; a cheaper path to a known node updates it and keeps its entry order |
| Path | includes the start cell; `length` is the number of moves |
| DFS | stack; children are pushed in reverse order so the first successor is expanded first; no depth limit (the visited set guarantees termination) |

Metrics reported (RF-15, RF-38; same keys as Appendix B): `exito`, `camino`, `costo`,
`longitud`, `estados_generados`, `estados_expandidos`, `maximo_frontera`, `tiempo_segundos`.
`maximo_frontera` counts distinct states waiting in the frontier. The time is wall-clock and
the only non-deterministic field.

### 6.3 Complexity

Variables: `b` branching factor (≤ 4 for one unit), `d` depth of the shallowest solution, `m`
maximum depth, `V` = number of reachable states = at most rows × columns in the single-unit
model, `k` beam width, `L` number of levels, `U` units per side, `D` Minimax depth in plies.

| Algorithm | Complete | Optimal | Time | Space |
|---|---|---|---|---|
| BFS | yes | in moves (optimal cost only if all costs are equal) | O(min(b^d, V)) | O(min(b^d, V)) |
| DFS | yes (graph search) | no | O(V) | O(V) |
| UCS | yes (positive costs) | yes | O(V log V) | O(V) |
| A\* | yes | yes with an admissible and consistent h | O(V log V) worst case; fewer expansions with a good h | O(V) |
| Beam (k) | **no** | no | O(L · k · b · log(k·b)) | O(k · b) |
| Minimax | with depth limit | exact for the horizon | O(B^D), B ≤ 4U (four moves per unit) | O(D) |
| Alpha-beta | same decision as Minimax | same | O(B^(D/2)) best case, O(B^D) worst | O(D) |

The `log` factors come from the binary heap used for the priority queues. The single-unit
searches are bounded by the number of cells because the search state is the position; in the
full game the state space is much larger (positions of every unit × carrier × turn), which is
why Minimax is depth-limited.

### 6.4 Beam Search (G9)

Level by level. At each level all successors of the kept nodes are generated; only the `k`
with the smallest `f = g + h` survive, ties broken by generation order. A state kept in a
previous level is not generated again. It is **incomplete**: pruning may remove the only
promising branch. `maximo_frontera` counts candidates *before* pruning. `k = 1, 2, 4, 8` are
experimented (RF-23); the result is in section 10.3.

### 6.5 Minimax and alpha-beta (G11)

- MAX is the side to move at the root. One unit of depth is **one action of one side**, so
  the two sides alternate by ply.
- Leaves are terminal states and nodes at the depth limit; utility is evaluated there.
- Both algorithms share one recursion; alpha-beta only adds the cut `alpha ≥ beta`.
- At the root the first action (in the given order) with a *strictly* higher value wins, so
  Minimax and alpha-beta pick the same action in ties (RF-31).
- Metrics (RF-30): `nodos_generados` (child states produced), `nodos_evaluados` (utility
  calls), `nodos_podados` (sibling actions skipped by a cut), `profundidad_alcanzada`, time,
  chosen action, root value and the value of every root action.
- Action order is configurable: `default` (up, down, left, right per unit) or `reversed`
  (RF-32). The depth is read from the JSON (`juego.profundidad_maxima_minimax`) or `--depth`
  and never needs code changes (RF-26).
- The values reported for root actions after the best one in alpha-beta may be bounds, not
  exact values.
- The assignment suggests extra adversarial actions (block, protect...). The team chose
  *move* only; interception is a consequence of movement, not an action, which
  keeps the branching factor low.

## 7. Heuristics (RF-21, RF-22)

Both heuristics are admissible and consistent for four-direction moves.

### 7.1 h1 — Manhattan

| Point | Answer |
|---|---|
| 1. What it estimates | Remaining cost if the map had no obstacles and every step cost the cheapest passable terrain |
| 2. State information used | Position of the moving unit, the goal cell, and the cheapest step cost of the scenario |
| 3. Computational cost | O(1) per evaluation, no preprocessing |
| 4. Admissible? | Yes. Each move changes the Manhattan distance by at most 1 and costs at least the minimum step cost, so `h(n) ≤ h*(n)`. Consistent for the same reason |
| 5. Where it guides well / loses discrimination | Guides well on open terrain. Behind a barrier it still points straight at the goal and A\* wastes expansions on the wrong side of the wall (case 3). It also cannot tell cheap from expensive terrain except through the global minimum cost |

### 7.2 h2 — Obstacle-aware (BFS-based)

| Point | Answer |
|---|---|
| 1. What it estimates | Remaining cost if every step cost the minimum, but walls and the rival base cannot be crossed |
| 2. State information used | Unit position and the passability layout of the board (walls, rival base), plus the minimum step cost. Not terrain costs or other units |
| 3. Computational cost | One backward BFS from the goal when the problem is built: O(R·C). Then O(1) per evaluation (table lookup). Cells that cannot reach the goal get ∞ |
| 4. Admissible? | Yes. It is the exact number of moves of a relaxed problem (free terrain cost = minimum) multiplied by a lower bound of the step cost. `h2 ≥ h1` everywhere and `h2 ≤ h*`. Consistent |
| 5. Where it guides well / loses discrimination | Guides well when walls or the rival base force detours (cases 3 and 4). It does not see terrain costs, so when the shortest route in moves crosses expensive terrain (the swamp in case 4) it still explores more than a perfect heuristic would. On an open map it equals h1 and adds only the preprocessing cost |

**Origin.** Claude Code proposed this second heuristic; the team reviewed and accepted it.
(Earlier notes and a docstring called it "the team's proposal"; that wording was corrected, see
section 14.)

Measured effect (cases 3 and 4, same cost for all three): expansions of UCS / h1 / h2 are
295 / 166 / 84 in case 3 and 332 / 186 / 115 in case 4.

## 8. Utility function (RF-27, RF-33)

Defined from the point of view of MAX (the side to move at the root); MAX maximizes it, MIN
minimizes it:

```
U = w_entrega  · (+1 if MAX delivered, −1 if MIN delivered)
  + w_carga    · (+1 if MAX carries, −1 if MIN carries)
  − w_dist     · (distance to the current objective)
  + w_rival    · (distance of the nearest rival to the carrier, only if MAX carries)
```

- **Objective:** MAX's base if MAX carries; the carrier if MIN carries (chase it); the
  resource cell if nobody carries it. Distance is Manhattan, measured from the nearest MAX
  unit (from the carrier itself when MAX carries).
- **Rival term:** only when MAX carries. A rival close to MAX's carrier lowers `U`
  (interception risk).
- **Weights:** `entrega = 10`, `recurso_cargado = 3`, `distancia_objetivo = 1`,
  `distancia_rival = 0.5`. They are read from the optional `utilidad` section of the JSON
  (RNF-02); the numbers above apply only to keys that are missing.
- **Why these weights:** delivery must dominate everything else (it ends the game); carrying is
  worth more than being close to the resource; each cell of distance costs one point so
  progress is always visible; the rival term breaks ties between equally distant routes in
  favor of safer ones.

**Explaining a decision (RF-33).** In case 7 depth 1 grabs the resource (U = 3) and depth 2
still prefers it, but its value drops to 0 because B1 steps next to the carrier and the
resource falls. Depth 3 finds that moving A1 to (1,1) first leaves B1 no free neighbor of the
resource cell before A2 grabs it, so the carrier keeps it (U = 3 − 1 + 0.5·2 = 3). Doubling
`distancia_rival` would make safe routes even more attractive; setting `distancia_objetivo`
to 0 would remove the incentive to approach at all.

**Known limitation.** With 10 / 3 / 1 / 0.5 a resource dropped under one of MAX's own units
(U = 0) is valued above carrying it more than 3 cells from the base (U < 0). In addition,
even depths let the opponent answer last and flatten many values to 0 (case 10). Both effects
are consequences of the weights and of the horizon, not of the algorithms. The team decided on
2026-10-17 not to change the defaults (it would invalidate the validated cases 7–10); a
scenario that needs another behavior sets, for example, `recurso_cargado ≥ 8` in its
`utilidad` section.

## 9. Open decisions of the assignment (G1–G15)

| # | Decision | Where it is justified |
|---|---|---|
| G1 | Python 3.14 with `uv`; `pytest`, `ruff`, `mypy --strict`; GUI with `tkinter` (standard library, no new dependency) | decisions 2026-10-07, 2026-10-16 |
| G2 | Four directions; Manhattan is admissible | 2026-10-07 |
| G3 | Cost paid on entering the destination cell; start cell free | 2026-10-07, 2026-10-14 |
| G4 | One unit per cell; the rival base cannot be entered; bases and the resource cell can be stepped on when free. Interception = a rival adjacent to the carrier after any move | 2026-10-07, 2026-10-14 |
| G5 | The carrier drops the resource on its own cell when intercepted (no transfer) | 2026-10-14 |
| G6 | Draw at the turn limit (`juego.limite_turnos`, default 100); a side without moves passes its turn | 2026-10-07, 2026-10-14 |
| G7 | Graph search with visited set; DFS without depth limit | 2026-10-14 |
| G8 | Expansion order up/down/left/right; first-in-first-out tie-break for every algorithm | 2026-10-14 |
| G9 | Beam by levels, keeps the `k` smallest `f = g + h` | 2026-10-16 |
| G10 | Optional `prueba` fields: `algoritmo`, `heuristica` (`H1` / `H2`), `k`, `orden_acciones`; canonical names `BFS`, `DFS`, `UCS`, `A_STAR` (alias `A*`, `A_ESTRELLA`), `BEAM`, `MINIMAX`, `ALPHA_BETA`; command-line options override the JSON | 2026-10-17 |
| G11 | Utility from the MAX side; depth counted in actions of one side; win/loss ±10 | 2026-10-16, 2026-10-17 |
| G12 | Costs may be integers or decimals; bands `A`/`a` are accepted and normalized | 2026-10-07 |
| G13 | Target of 5 s per Minimax decision with configurable depth; maximum map for Minimax 15×15 (measured, see 10.5) | 2026-10-16, 2026-10-17 |
| G14 | Documents in English, Markdown; delivery 2026-10-21 | this report |
| G15 | Team of two | this report |

The questions of assignment section 19 have no official answer yet; the decisions above are the
documented assumptions. If the professor answers differently, only the rules in `domain/` and
the loader defaults change; the algorithms take everything from the scenario.

## 10. Experimental methodology and results

### 10.1 Method

- **Scenarios:** the official Appendix A example and the team's scenarios in `scenarios/`
  (`caso_01` … `caso_07`, `prueba_20x20`).
- **Deterministic metrics:** generated, expanded, frontier size, cost, length, nodes evaluated
  and pruned do not depend on the machine. The expected values were derived by hand from each
  map **before** running the code (comments in `tests/test_cases_f2.py`, `test_cases_f3.py`,
  `test_cases_f4.py`) and are asserted by the tests.
- **Time:** wall-clock via `time.perf_counter`, reported in seconds. It varies between runs and
  machines; it is used only to compare orders of magnitude. No randomness is used anywhere.
- **Reproduction:** every number below can be regenerated with the commands in
  [`user-manual.md`](user-manual.md), section 6; the raw CSV/JSON used for this report is in
  `docs/results/`.

### 10.2 Uninformed and cost-based searches (cases 1 and 2)

| Case | Algorithm | Cost | Moves | Generated | Expanded | Max frontier |
|---|---|---|---|---|---|---|
| 1 | BFS | 4 | 4 | 39 | 29 | 11 |
| 1 | DFS | 42 | 42 | 152 | 94 | 58 |
| 1 | UCS | 4 | 4 | 39 | 29 | 11 |
| 2 | BFS | 25 | 7 | 126 | 104 | 23 |
| 2 | DFS | 153 | 87 | 396 | 287 | 171 |
| 2 | UCS | 17 | 17 | 269 | 239 | 33 |

Case 1 (all cost 1): BFS and UCS coincide; DFS finds a valid but 10× longer path. Case 2 has a
swamp band of cost 7: BFS minimizes moves (7) but pays 25; UCS goes around for 17 moves and
pays 17. Shortest in moves ≠ cheapest.

### 10.3 Informed and limited-memory searches (cases 3, 4 and 5)

| Case | Algorithm | Cost | Moves | Generated | Expanded | Max frontier |
|---|---|---|---|---|---|---|
| 3 | UCS | 29 | 29 | 307 | 295 | 17 |
| 3 | A\* h1 | 29 | 29 | 194 | 166 | 28 |
| 3 | A\* h2 | 29 | 29 | 122 | 84 | 38 |
| 4 | UCS | 24 | 22 | 346 | 332 | 20 |
| 4 | A\* h1 | 24 | 22 | 230 | 186 | 44 |
| 4 | A\* h2 | 24 | 22 | 164 | 115 | 49 |

Both heuristics return the optimal cost; h2 expands about half as many states in case 3
because it sees the wall. In case 4 the cheap gap is the long one and the short gap crosses a
swamp: h2 helps (115 vs. 186) but cannot see the swamp, so it does not reach the minimum
possible effort. The frontier of A\* is larger than UCS's because it keeps more nodes alive
while diving toward the goal.

Beam Search on case 5 (optimal cost 28 in 14 moves, from UCS):

| k | Success | Cost | Moves | Generated | Expanded | Max frontier |
|---|---|---|---|---|---|---|
| 1 | **no** | — | — | 9 | 5 | 3 |
| 2 | yes | 30 | 16 | 43 | 29 | 6 |
| 4 | yes | 28 | 14 | 50 | 41 | 6 |
| 8 | yes | 28 | 14 | 46 | 44 | 6 |

This answers RF-24: restricting the alternatives **can discard a better path**. With `k = 1`
the only kept candidate leads into a dead end and the search fails; with `k = 2` it survives
but keeps a worse route (30 > 28); `k = 4` and `k = 8` recover the optimum. More width costs
more expansions, and past a point it buys nothing (k = 8 expands more than k = 4 for the same
path).

### 10.4 Adversarial decision (cases 7–10)

Scenario `caso_07_decision_adversarial.json`: 5×7 open map, two units per side, resource at
(0,1), A moves first, default weights. `GRAB` = A2→(0,1); `GUARD` = A1→(1,1).

| Algorithm | Depth | Order | Action | Value | Generated | Evaluated | Pruned |
|---|---|---|---|---|---|---|---|
| Minimax | 1 | default | GRAB | 3 | 5 | 5 | 0 |
| Minimax | 2 | default | GRAB | 0 | 41 | 36 | 0 |
| Minimax | 3 | default | GUARD | 3 | 234 | 193 | 0 |
| Minimax | 4 | default | A1→(0,0) | 0 | 1,616 | 1,388 | 0 |
| Minimax | 5 | default | A1→(0,0) | 0 | 8,626 | 7,016 | 0 |
| Alpha-beta | 1 | default | GRAB | 3 | 5 | 5 | 0 |
| Alpha-beta | 2 | default | GRAB | 0 | 23 | 18 | 18 |
| Alpha-beta | 3 | default | GUARD | 3 | 80 | 58 | 48 |
| Alpha-beta | 3 | reversed | GUARD | 3 | 96 | 67 | 78 |
| Alpha-beta | 4 | default | A1→(0,0) | 0 | 239 | 165 | 271 |
| Alpha-beta | 4 | reversed | GRAB | 0 | 315 | 239 | 209 |
| Alpha-beta | 5 | default | A1→(0,0) | 0 | 788 | 577 | 393 |
| Alpha-beta | 5 | reversed | GRAB | 0 | 1,370 | 996 | 683 |

- **Case 7:** the best decision is not to grab the resource first (depth 1 and 2 grab; depth 3
  guards).
- **Case 8:** at depth 4 alpha-beta chooses the same action and value as Minimax while
  generating 239 nodes instead of 1,616 (≈ 7×) and evaluating 165 instead of 1,388.
- **Case 9:** at depth 3 the same decision with `default` order generates 80 nodes and with
  `reversed` 96: the order changes the amount of pruning but not the decision. At depth 4
  the reversed order also changes the tie-break among equal values (0), hence a different
  action with the same value.
- **Case 10:** depths 1 and 3 end on A's move, so grabbing (1) or guarding (3) looks safe
  (value 3); from depth 4 B has enough replies to intercept whatever A does and every value
  flattens to 0, so the first action in order wins the tie. This is the horizon effect
  mentioned in section 8.

### 10.5 Performance (G13)

Scenario `prueba_15x15.json` (15×15, swamp cells and a wall, three units per side); depth
counted in actions of one side; raw data in `docs/results/rendimiento_15x15*.csv`:

| Algorithm | Depth | Time |
|---|---|---|
| Alpha-beta | 5 | 0.02 s |
| Alpha-beta | 6 | 0.09 s |
| Alpha-beta | 7 | 0.36 s |
| Minimax | 5 | 0.34 s |
| Minimax | 6 | 3.4 s |

On the 20×20 test scenario
(`prueba_20x20.json`, three units per side) alpha-beta at depth 2…6 takes ≤ 0.10 s
(`docs/results/rendimiento_20x20.csv`). Conclusion: within the 5 s target, alpha-beta up to
depth 7 and plain Minimax up to depth 6. Times are from the team's laptop (Windows, Python 3.14).

## 11. Verification and testing (RF-42, RE-03)

The `--verify` option (and the GUI checkbox) runs the six checks of the assignment:

| # | Check | Applies to |
|---|---|---|
| 1 | every move is valid | searches |
| 2 | no unit crosses an obstacle | searches |
| 3 | the reported cost equals the sum of the transitions | searches |
| 4 | the final state meets the goal | searches |
| 5 | no invalid states are generated | searches |
| 6 | the actions considered by Minimax / alpha-beta are legal and the chosen one is legal | adversarial |

Every run saved in `docs/results/` was produced with `--verify` and all checks pass.

Automated tests (`uv run pytest`): domain rules and state, scenario validation (the nine
validations and the atomic load), search algorithms, heuristics, utility, Minimax / alpha-beta,
verifier, runner and sweeps, the 10 cases with their expected values, and the GUI session and
window. `uv run ruff check .` and `uv run mypy src` pass (strict).

## 12. Scenario format and robustness (RF-34 … RF-37)

The loader reads the JSON of Appendix A, validates **all** of it (the nine minimum validations
plus: two units cannot share a cell, `limite_turnos` and `utilidad` are well-formed) and reports
every error before rejecting the file; nothing is built if any error exists. Optional fields of
the team (`juego.limite_turnos`, `utilidad`, `prueba.algoritmo`, `prueba.heuristica`,
`prueba.k`, `prueba.orden_acciones`) never alter the mandatory ones. The loader does not require
three units per side, because Appendix A has two; the team's own scenarios use three or more
where the size allows it. Terrain names are read from the catalog (open set); non-passable
terrains may omit `costo`. Dimensions, costs, bases, obstacles, units and resource may change
without touching the code; this is exercised by scenarios of 4×4, 5×7, 7×9, 20×20 and a
generated 15×15.

## 13. Limitations

1. **Student validation is pending.** The cross-review fields in the docstrings still say
   "pending cross-review by the other team member"; they will be completed by the reviewer
   after reading and testing each method.
2. **Utility weights** have the limitation described in section 8; they are configurable per
   scenario but the defaults were not retuned.
3. **Minimax cost** grows exponentially: plain Minimax above depth 5 on 15×15 maps exceeds the
   5 s target; alpha-beta depth 7 and beyond depends heavily on action order.
4. **Single-unit searches** ignore the adversary and the resource by design (RF-14); they do
   not model a plan of the whole game.
5. **Only one action** (move); no wait, protect or block actions (decisions of 2026-10-07 and 2026-10-17).
6. **Explored states** are not displayed in the GUI (RF-41, optional).
7. **Questions to the professor** (assignment section 19) have no official answer.
8. **Measured times** come from one machine and are not repeated statistically; deterministic
   metrics are the basis for comparisons.

## 14. Report of generative-AI use

**Tool:** Claude Code (model Claude Sonnet 5.5) in the team's repository, used by Daniel Felipe
Franco Rincón. **Purpose, by area:**

| Area | What the AI did | What the team did |
|---|---|---|
| Context and process | Proposed the layout of `.context/` (state, decisions, handoffs) and the work phases | Approved and used it; recorded every decision in `decisions.md` |
| Decisions | Proposed options for stack, rules, utility function, GUI library, time target, export format and calendar | Chose between the options (each is marked "proposed by Claude, approved by Daniel" or "decided by the user") |
| `domain/`, `scenario/` | Drafted the code from `rules.md` | Defined the rules; required the extra validation of shared cells |
| BFS, DFS, UCS, A\*, Beam, verifier | Drafted the code and tests | Defined conventions (graph search, tie-break, Beam criterion); expected values of the cases were derived by hand before running |
| Heuristics | **Proposed the second heuristic (`obstacle_aware`, BFS-based)** and drafted both | Accepted it after checking admissibility |
| Utility, Minimax, alpha-beta | Drafted the code; proposed the formula and weights | Approved the formula; the sign of the rival term was corrected during review (see below) |
| CLI, runner, sweeps, export | Drafted the code | Decided the option names (G10) and the formats |
| GUI | Drafted `gui/session.py` and `gui/app.py`, including the Spanish interface and the automatic mode | Requested the features and the language; reviews the behavior |
| Scenarios and experiments | Generated the 15×15 and 20×20 maps with a script; ran the sweeps | Chose the case maps and the expected values |
| Documentation | Drafted this report, the manual and the case table from the repository and the experiment output | Reviews and takes responsibility for the content |

**Human interventions and corrections of the AI draft:**

- The decision text for the utility gave a single negative rival term; the implementation makes
  the sign depend on who carries the resource (a rival near the *opponent's* carrier is not a
  threat to MAX).
- The first model of the searches treated rivals as obstacles, which left the official example
  without a solution; the team changed it to remove the rivals (section 6.1).
- A documentation inconsistency was found: a docstring and a decision called `obstacle_aware`
  "the team's proposal" when Claude proposed it. The wording was corrected.
- Tests and expected values for cases 1–10 were checked against hand-derived values; the
  cross-review of `domain/`, `scenario/` and `algorithms/` by the other team member is pending.

**Method docstrings:** each relevant method states `AI usage`, `AI intervention` and
`Student validation` (assignment section 9.2). The first two are complete; the third is the
pending item of section 13.

**Responsibility.** Both team members are responsible for the entire code and must be able to
explain, modify and defend any part of it.

## 15. Reproducibility and versions (RE-02, RE-03, RE-04)

- Install and run: see the user manual. Python 3.14 and `uv`; dependencies fixed by `uv.lock`
  (`pytest` 9.1.1, `ruff` 0.16.10, `mypy` 2.4.0).
- Initial states are declared in the JSON files of `scenarios/`.
- Expected vs. obtained for every case: [`cases.md`](cases.md).
- Raw results: `docs/results/*.csv` and `*.json`.
- The delivered version is marked with the Git tag `entrega-2026-10-21`; this report, the manual
  and the code correspond to that tag.
