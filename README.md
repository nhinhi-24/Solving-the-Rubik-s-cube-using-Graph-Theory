## Solving the Rubik's cube using Graph Theory

## Setup
Python 3.10 or newer.

```
pip install pytest numpy
python -m pytest -q        # should print: 81 passed
python demo.py             # scrambles a cube, prints it, undoes it
```

## The cube module (`cube/`)
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

## Rules
- Never change `cube/` without telling the group and re-running all tests.
- One branch per person; merge by pull request reviewed by another member.
- `python -m pytest -q` must pass before every merge.
