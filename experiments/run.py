import argparse
import csv
import multiprocessing as mp
import random
import sys
import time
import tracemalloc
from functools import partial
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from cube.cube import SOLVED, apply_sequence, is_solved, parse, random_scramble

def mock_bfs_solve(state: bytes, max_depth: int, sleep_sec: float = 0.001):
    time.sleep(sleep_sec)
    return ["U"] * max_depth, 18 ** min(max_depth, 2)


def get_solver(name: str, mock_sleep: float = 0.001):
    solvers = {
        "bfs": partial(mock_bfs_solve, sleep_sec=mock_sleep),  # Đổi thành bfs_solve khi có T06
        # "iddfs": iddfs_solve,
        # "bidirectional": bidirectional_solve,
    }
    if name not in solvers:
        raise ValueError(f"Unsupported algorithm: {name}")
    return solvers[name]


def generate_scrambles(lengths: list[int], num_per_length: int, seed: int):
    master_rng = random.Random(seed)
    dataset = []
    for length in lengths:
        for trial in range(num_per_length):
            sub_seed = master_rng.randint(0, 2**32 - 1)
            scramble_str = random_scramble(length, seed=sub_seed)
            state = apply_sequence(SOLVED, scramble_str)
            dataset.append((length, trial, scramble_str, state))
    return dataset


def _worker(algo_name: str, state: bytes, max_depth: int, mock_sleep: float, queue: mp.Queue):
    solver = get_solver(algo_name, mock_sleep=mock_sleep)
    tracemalloc.start()
    t0 = time.perf_counter()

    solution, nodes_expanded = solver(state, max_depth=max_depth)

    elapsed = time.perf_counter() - t0
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    queue.put({
        "solution": solution,
        "nodes_expanded": nodes_expanded,
        "time_sec": elapsed,
        "peak_memory_kb": peak_bytes / 1024.0,
    })


def run_with_timeout(algo_name: str, state: bytes, max_depth: int, time_limit: float, mock_sleep: float):
    queue = mp.Queue()
    proc = mp.Process(
        target=_worker,
        args=(algo_name, state, max_depth, mock_sleep, queue),
    )
    proc.start()
    proc.join(timeout=time_limit)

    if proc.is_alive():
        proc.terminate()
        proc.join()
        return {
            "solved": False,
            "valid": False,
            "timed_out": True,
            "solution_length": "",
            "time_sec": round(time_limit, 6),
            "nodes_expanded": "",
            "peak_memory_kb": "",
        }

    res = queue.get()
    sol = res["solution"]
    if sol is not None:
        moves = parse(sol)
        sol_len = len(moves)
        valid = is_solved(apply_sequence(state, moves))
    else:
        sol_len = ""
        valid = False

    return {
        "solved": sol is not None,
        "valid": valid,
        "timed_out": False,
        "solution_length": sol_len,
        "time_sec": round(res["time_sec"], 6),
        "nodes_expanded": res["nodes_expanded"],
        "peak_memory_kb": round(res["peak_memory_kb"], 2),
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark Rubik's Cube search algorithms.")
    parser.add_argument("--algo", default="bfs", choices=["bfs", "iddfs", "bidirectional"])
    parser.add_argument("--min-len", type=int, default=1)
    parser.add_argument("--max-len", type=int, default=4)
    parser.add_argument("--num-scrambles", type=int, default=50)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--time-limit", type=float, default=120.0)
    parser.add_argument("--output", type=Path, default=Path("results.csv"))
    parser.add_argument("--mock-sleep", type=float, default=0.001)
    return parser.parse_args()


def main():
    args = parse_args()
    lengths = list(range(args.min_len, args.max_len + 1))
    dataset = generate_scrambles(lengths, args.num_scrambles, args.seed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "algorithm",
        "scramble_length",
        "trial",
        "seed",
        "scramble",
        "solved",
        "valid",
        "timed_out",
        "solution_length",
        "time_sec",
        "nodes_expanded",
        "peak_memory_kb",
    ]

    write_header = not args.output.exists()
    with args.output.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for length, trial, scramble_str, state in dataset:
            metrics = run_with_timeout(
                args.algo,
                state,
                max_depth=length,
                time_limit=args.time_limit,
                mock_sleep=args.mock_sleep,
            )
            writer.writerow({
                "algorithm": args.algo,
                "scramble_length": length,
                "trial": trial,
                "seed": args.seed,
                "scramble": scramble_str,
                **metrics,
            })
            f.flush()

    print(f"Completed {len(dataset)} runs -> {args.output}")

if __name__ == "__main__":
    main()