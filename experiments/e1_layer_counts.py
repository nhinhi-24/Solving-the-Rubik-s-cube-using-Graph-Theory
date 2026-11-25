"""Count states per depth with BFS"""
import csv
import os
from cube import SOLVED, MOVE_NAMES, apply_move, allowed_after


def count_states_by_depth(max_depth: int = 6) -> list[dict]:
    visited = {SOLVED} 
    current_layer = [(SOLVED, None)] 
    results = [
        {
            "depth": 0,
            "exact_count": 1,
            "paper_formula":1,

        }
    ]

    for d in range(1, max_depth + 1):
        next_layer = []

        for state, last_move in current_layer:
            possible_moves = MOVE_NAMES if last_move is None else allowed_after(last_move)

            for move in possible_moves:
                new_state = apply_move(state, move)

                if new_state not in visited:
                    visited.add(new_state)
                    next_layer.append((new_state, move))

        exact_count = len(next_layer)
        paper_count = 18 * (15 ** (d - 1))

        print(f"Depth {d}: Exact = {exact_count:,} | Paper formula = {paper_count:,}")
        results.append(
            {
                "depth": d,
                "exact_count": exact_count,
                "paper_formula": paper_count,
            }
        )

        current_layer = next_layer

    return results

# save data 
def save_layer_counts(results: list[dict], filepath: str = "data/layer_counts.csv") -> None:
    """Save the layer count results to a CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["depth", "exact_count", "paper_formula"])
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved results to: {filepath}")


if __name__ == "__main__":
    data = count_states_by_depth(max_depth=6)
    save_layer_counts(data)



