# The 10 minimum demonstration cases — expected vs. obtained

Section 13 of the assignment. Every expected value below was **derived by hand from the map
before running the code**; the same values are asserted by the automated tests
(`tests/test_cases_f2.py`, `test_cases_f3.py`, `test_case_6.py`, `test_cases_f4.py`), so
`uv run pytest` re-checks the whole table. "Obtained" values come from the CLI runs saved in
[`results/`](results/) (every run was executed with `--verify` and all checks passed). Time is
not listed: it is the only non-deterministic metric.

All search scenarios are 20×20 (case 5: 7×9) with three units per side; searches use unit `A1`
(`prueba.unidad_inicio`). Initial state of each case = the JSON file named in the table.

| # | Scenario file | Command (copy and run) |
|---|---|---|
| 1 | `scenarios/caso_01_bfs_vs_dfs.json` | `uv run python -m tactical_grid scenarios/caso_01_bfs_vs_dfs.json --algorithm BFS,DFS --verify` |
| 2 | `scenarios/caso_02_bfs_vs_ucs.json` | `uv run python -m tactical_grid scenarios/caso_02_bfs_vs_ucs.json --algorithm BFS,UCS --verify` |
| 3 | `scenarios/caso_03_obstaculo_heuristica.json` | `uv run python -m tactical_grid scenarios/caso_03_obstaculo_heuristica.json --algorithm UCS,A_STAR --heuristic H1,H2 --verify` |
| 4 | `scenarios/caso_04_comparacion_heuristicas.json` | `uv run python -m tactical_grid scenarios/caso_04_comparacion_heuristicas.json --algorithm UCS,A_STAR --heuristic H1,H2 --verify` |
| 5 | `scenarios/caso_05_beam_k.json` | `uv run python -m tactical_grid scenarios/caso_05_beam_k.json --algorithm UCS,BEAM --k 1,2,4,8 --verify` |
| 6 | 5×7 map built by the test (`tests/helpers.py::mini_race`) | `uv run pytest tests/test_case_6.py` |
| 7 | `scenarios/caso_07_decision_adversarial.json` | `uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm MINIMAX --depth 1,2,3 --verify` |
| 8 | `scenarios/caso_07_decision_adversarial.json` | `uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm MINIMAX,ALPHA_BETA --depth 4 --verify` |
| 9 | `scenarios/caso_07_decision_adversarial.json` | `uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm ALPHA_BETA --depth 3 --order default,reversed --verify` |
| 10 | `scenarios/caso_07_decision_adversarial.json` | `uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm ALPHA_BETA --depth 1,2,3,4,5 --verify` |

(Cases 7 to 10 share one map: 20×20, mostly open ground (cost 1) with a few swamps (cost 3) and a
wall with a gap, three units per side, resource at (8,11), A1 (9,11), A2 (7,8), A3 (7,11),
B1 (10,8), B2 (12,11), B3 (12,8), A moves first, default utility weights
10 / 3 / 1 / 0.5 / 0.5. Case 6 uses a small 5×7 race that the test builds.)

---

## Case 1 — BFS vs. DFS

**Setup.** All cells `camino` (cost 1). A1 at (2,2), goal (2,6).
**Expectation.** Both find a solution but explore differently. BFS returns the straight route:
4 moves, cost 4. DFS, which expands "down" first, reaches the goal by a much longer path.

| Algorithm | Expected | Cost | Moves | Generated | Expanded | Max frontier | Match |
|---|---|---|---|---|---|---|---|
| BFS | 4 moves, cost 4 | 4 | 4 | 39 | 29 | 11 | yes |
| DFS | success, longer path, different expansion | 42 | 42 | 152 | 94 | 58 | yes |

Conclusion: same space, different traversal; DFS is complete here but not optimal.

## Case 2 — Short route vs. cheap route

**Setup.** A swamp band (cost 7) on columns 8–10, rows 0–9. A1 at (5,5), goal (5,12).
**Expectation.** BFS crosses the band: 7 moves with cost 4·1 + 3·7 = 25. UCS goes around it
through row 10: 17 moves, cost 17.

| Algorithm | Expected | Cost | Moves | Generated | Expanded | Max frontier | Match |
|---|---|---|---|---|---|---|---|
| BFS | 7 moves, cost 25 | 25 | 7 | 126 | 104 | 23 | yes |
| UCS | 17 moves, cost 17 | 17 | 17 | 269 | 239 | 33 | yes |

Conclusion: the path with fewest moves is not the cheapest.

## Case 3 — Obstacle and heuristic

**Setup.** A wall on column 8, rows 0–15. A1 at (5,5), goal (5,12): the goal is 7 cells away
but the only way is around the wall's bottom end (row 16).
**Expectation.** Every optimal algorithm needs 11 down + 7 right + 11 up = 29 moves, cost 29.
Manhattan is fooled by the wall; the obstacle-aware heuristic is not, so expansions order as
h2 < h1 < UCS.

| Algorithm | Expected cost / moves | Cost | Moves | Generated | Expanded | Max frontier | Match |
|---|---|---|---|---|---|---|---|
| UCS | 29 / 29 | 29 | 29 | 307 | 295 | 17 | yes |
| A\* h1 | 29 / 29 | 29 | 29 | 194 | 166 | 28 | yes |
| A\* h2 | 29 / 29, path passes (16,8) | 29 | 29 | 122 | 84 | 38 | yes |

## Case 4 — Comparison of heuristics

**Setup.** A wall on column 9, rows 3–16. The top gap (rows 0–2) is swamp (cost 3); the
bottom gap is open ground. A1 at (9,5), goal (9,13).
**Expectation.** Optimal cost 24 over 22 moves for UCS and for A\* with either heuristic. h2
expands fewer states than h1 because it sees the wall, but it cannot see the swamp, so it still
explores more than a perfect heuristic would.

| Algorithm | Expected cost / moves | Cost | Moves | Generated | Expanded | Max frontier | Match |
|---|---|---|---|---|---|---|---|
| UCS | 24 / 22 | 24 | 22 | 346 | 332 | 20 | yes |
| A\* h1 | 24 / 22 | 24 | 22 | 230 | 186 | 44 | yes |
| A\* h2 | 24 / 22, fewer than h1 | 24 | 22 | 164 | 115 | 49 | yes |

## Case 5 — Beam Search and k

**Setup.** 7×9 map with grass (cost 2) and forest (cost 4). A1 at (0,0), goal (6,8). The
optimal cost is 28 over 14 moves (UCS).
**Expectation.** `k = 1` prunes the only promising branch and fails. `k = 2` survives but keeps
a worse route (cost 30, 16 moves): the pruning discarded a better path. `k = 4` and `k = 8`
recover the optimum.

| k | Expected | Success | Cost | Moves | Generated | Expanded | Max frontier | Match |
|---|---|---|---|---|---|---|---|---|
| 1 | fails | no | — | — | 9 | 5 | 3 | yes |
| 2 | cost 30, 16 moves | yes | 30 | 16 | 43 | 29 | 6 | yes |
| 4 | cost 28, 14 moves | yes | 28 | 14 | 50 | 41 | 6 | yes |
| 8 | cost 28, 14 moves | yes | 28 | 14 | 46 | 44 | 6 | yes |

## Case 6 — Composite state

**Setup.** 5×7 open map (`mini_race` in `tests/helpers.py`); A1 stands at (1,0), next to its
base (0,0).
**Expectation.** The same unit on the same cell gives *different states* when the extra game
information differs, and the difference changes what the rules produce:

| State | Position of A1 | Carrier | Turn | Effect of `Move A1 → (0,0)` |
|---|---|---|---|---|
| free (initial) | (1,0) | nobody | A | enters the base, no winner |
| carrying | (1,0) | A1 | A | enters the base and **side A wins** |
| rival turn | (1,0) | nobody | B | A1 has **no legal action** |

**Obtained** (`tests/test_case_6.py`): the three states have equal `positions` but are
different objects (`len(set(states)) == 3`); `winner` is `None` after the free move and `A`
after the carrying move; A1 has no legal action in the rival-turn state; a dictionary keyed by
state keeps three entries while keyed by position it would keep one. Match: yes.

## Case 7 — Adversarial decision

**Expectation.** The best decision according to Minimax is not the first obvious advance. A1 and
A3 are both next to the resource, so at depth 1 the two grabs have the same value (−2.5) and the
first in action order (A1) wins; at depth 2 it still does (−3.5). From depth 3 the rivals'
approach from the south is inside the horizon: grabbing with A3 leaves A1 between the carrier
and the rivals and is worth −1.0, while grabbing with A1 or any other first move is worth −3.5.

| Depth | Expected action | Expected value | Obtained action | Obtained value | Match |
|---|---|---|---|---|---|
| 1 | A1 → (8,11) | −2.5 | A1 → (8,11) | −2.5 | yes |
| 2 | A1 → (8,11) | −3.5 | A1 → (8,11) | −3.5 | yes |
| 3 | A3 → (8,11) | −1.0 | A3 → (8,11) | −1.0 | yes |

## Case 8 — Minimax vs. alpha-beta

**Expectation.** Same action and value; alpha-beta evaluates part of the tree only.

| Depth 4 | Action | Value | Generated | Evaluated | Pruned | Match |
|---|---|---|---|---|---|---|
| Minimax | A3 → (8,11) | −2.0 | 14,896 | 13,501 | 0 | yes |
| Alpha-beta | A3 → (8,11) | −2.0 | 1,440 | 1,064 | 2,557 | yes |

Same decision with about 10× fewer generated nodes.

## Case 9 — Action order

**Expectation.** The decision is the same, the amount of pruning changes.

| Depth 3 | Action | Value | Generated | Evaluated | Pruned | Match |
|---|---|---|---|---|---|---|
| `default` order | A3 → (8,11) | −1.0 | 486 | 412 | 273 | yes |
| `reversed` order | A3 → (8,11) | −1.0 | 304 | 262 | 153 | yes |

Reversing the order changed the generated nodes from 486 to 304.

## Case 10 — Depth

**Expectation.** The value follows the horizon (even depths let B answer last), the decision
settles on A3 from depth 3, and the effort grows exponentially with the depth.

| Depth | Action | Value | Evaluated | Max depth reached | Match |
|---|---|---|---|---|---|
| 1 | A1 → (8,11) | −2.5 | 11 | 1 | yes |
| 2 | A1 → (8,11) | −3.5 | 25 | 2 | yes |
| 3 | A3 → (8,11) | −1.0 | 412 | 3 | yes |
| 4 | A3 → (8,11) | −2.0 | 1,064 | 4 | yes |
| 5 | A3 → (8,11) | 0.5 | 7,205 | 5 | yes |

(Alpha-beta, `default` order. With Minimax the evaluated nodes are 11 / 121 / 1,263 / 13,501 /
141,048.)

---

**Note.** These cases do not replace the professor's external tests. Appendix A of the
assignment (`scenarios/apendice_a.json`) is also run by the tests and by
`docs/results/apendice_a.csv` (all algorithms reach the goal at cost 14, except `BEAM` with
`k = 1`, which finds a longer route of cost 18).
