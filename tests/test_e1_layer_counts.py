"""Unit test for Exp.1"""
from experiments.e1_layer_counts import count_states_by_depth


def test_count_states_by_depth():
    results = count_states_by_depth(max_depth=4)
    exact_counts = [row["exact_count"] for row in results]
    assert exact_counts == [1, 18, 243, 3240, 43239]