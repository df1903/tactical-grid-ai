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
| 6 | `scenarios/caso_07_decision_adversarial.json` | `uv run pytest tests/test_case_6.py` |
| 7 | `scenarios/caso_07_decision_adversarial.json` | `uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm MINIMAX --depth 1,2,3 --verify` |
| 8 | `scenarios/caso_07_decision_adversarial.json` | `uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm MINIMAX,ALPHA_BETA --depth 4 --verify` |
| 9 | `scenarios/caso_07_decision_adversarial.json` | `uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm ALPHA_BETA --depth 3 --order default,reversed --verify` |
| 10 | `scenarios/caso_07_decision_adversarial.json` | `uv run python -m tactical_grid scenarios/caso_07_decision_adversarial.json --algorithm ALPHA_BETA --depth 1,2,3,4,5 --verify` |

(Cases 6 to 10 share one map: 5×7 open ground, cost 1, two units per side, resource at (0,1),
A1 (1,0), A2 (0,2), B1 (1,2), B2 (2,4), A moves first, default utility weights 10 / 3 / 1 / 0.5.)

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

**Setup.** Case-7 map; A1 stands at (1,0), next to its base (0,0).
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

**Expectation.** The best decision according to Minimax is not to go straight to the resource.
Greedy depth 1 grabs it with A2 → (0,1) (U = 3). Depth 2 still prefers it but its value falls to
0: B1 steps next to the carrier and the resource drops. Depth 3 finds that moving A1 → (1,1)
first leaves B1 no free neighbor of (0,1) before A2 grabs, so the carrier keeps the resource:
U = 3 − 1 + 0.5·2 = 3.

| Depth | Expected action | Expected value | Obtained action | Obtained value | Match |
|---|---|---|---|---|---|
| 1 | A2 → (0,1) | 3 | A2 → (0,1) | 3 | yes |
| 2 | A2 → (0,1) | 0 | A2 → (0,1) | 0 | yes |
| 3 | A1 → (1,1) | 3 | A1 → (1,1) | 3 | yes |

## Case 8 — Minimax vs. alpha-beta

**Expectation.** Same action and value; alpha-beta evaluates part of the tree only.

| Depth 4 | Action | Value | Generated | Evaluated | Pruned | Match |
|---|---|---|---|---|---|---|
| Minimax | A1 → (0,0) | 0 | 4,826 | 4,296 | 0 | yes |
| Alpha-beta | A1 → (0,0) | 0 | 431 | 299 | 757 | yes |

Same decision with about 11× fewer generated nodes.

## Case 9 — Action order

**Expectation.** The decision is the same, the amount of pruning changes.

| Depth 3 | Action | Value | Generated | Evaluated | Pruned | Match |
|---|---|---|---|---|---|---|
| `default` order | A1 → (1,1) | 3 | 142 | 110 | 106 | yes |
| `reversed` order | A1 → (1,1) | 3 | 191 | 148 | 145 | yes |

Reversing the order changed the generated nodes from 142 to 191.

## Case 10 — Depth

**Expectation.** Odd depths end on A's move, so the guard looks safe (value 3). At even depths B
gets one more reply and every value flattens to 0, so the first action in order wins the tie.
More depth costs exponentially more nodes.

| Depth | Action | Value | Evaluated | Max depth reached | Match |
|---|---|---|---|---|---|
| 1 | A2 → (0,1) | 3 | 7 | 1 | yes |
| 2 | A2 → (0,1) | 0 | 24 | 2 | yes |
| 3 | A1 → (1,1) | 3 | 110 | 3 | yes |
| 4 | A1 → (0,0) | 0 | 299 | 4 | yes |
| 5 | A1 → (1,1) | 3 | 1,583 | 5 | yes |

(Alpha-beta, `default` order. With Minimax the evaluated nodes are 7 / 64 / 467 / 4,296 /
30,994.)

---

**Note.** These cases do not replace the professor's external tests. Appendix A of the
assignment (`scenarios/apendice_a.json`) is also run by the tests and by
`docs/results/apendice_a.csv` (all algorithms reach the goal at cost 14, except `BEAM` with
`k = 1`, which finds a longer route of cost 18).
