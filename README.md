## Solving the Rubik's cube using graph theory

## Setup
Python 3.10 or newer.

```
pip install pytest numpy
python -m pytest -q        # should print: 81 passed
python demo.py             # scrambles a cube, prints it, undoes it
```

## The cube module (`cube/`): everyone uses only these functions
| Function | What it does |
|---|---|
| `SOLVED` / `solved()` | The solved cube (a 54-byte `bytes` object) |
| `MOVE_NAMES` | The 18 moves: `U U2 U' D D2 D' F F2 F' B B2 B' L L2 L' R R2 R'` |
| `apply_move(state, "R'")` | State after one move |
| `apply_sequence(state, "R U2 F'")` | State after a sequence |
| `inverse("R U2 F'")` | The sequence that undoes it: `"F U2 R'"` |
| `is_solved(state)` | True if solved |
| `cost(state)` | Paper's cost: number of stickers of the wrong colour (0–48) |
| `allowed_after(last_move)` | Moves allowed next (no same face twice; opposite faces in fixed order) |
| `random_scramble(length, seed)` | Reproducible random scramble |
| `to_string(state)` | Prints the cube as a net |

A state is `bytes`, so it can be put directly into a `set` or used as a `dict` key
(BFS visited set, the paper's HashMap, ...).

Sticker numbering, colours and move directions are explained at the top of `cube/cube.py`.

## What the tests already prove
- Every face turned 4 times = solved; every move followed by its inverse = solved.
- `R U R' U'` repeated 6 times = solved; opposite faces commute, adjacent ones do not.
- Moves turn the correct way (R brings the front up, U brings the right face to the front).
- One move changes exactly 20 stickers (used to prove the heuristic ⌈cost/20⌉ is admissible).
- Superflip has cost 24.
- **BFS from the solved cube gives exactly 1, 18, 243, 3,240, 43,239 states at depths 0–4**,
  matching the known values for the half-turn metric.

## Repository plan
```
cube/          cube model 
search/        bfs.py, dls.py, iddfs.py, bidirectional.py, pipeline.py, ida_star.py
pdb/           corner pattern database
data/          datasetA_states.csv, datasetB_runs.csv
experiments/   E1–E6 scripts
analysis/      make_figures.py
tests/         pytest tests (add a test file for every new module)
demo/          interactive viewer
```

## Team rules
- Never change `cube/` without telling the group and re-running all tests.
- One branch per person; merge by pull request reviewed by another member.
- `python -m pytest -q` must pass before every merge.
