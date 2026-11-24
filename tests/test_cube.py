import pytest

from cube import (solved, move_names, apply_move, apply_sequence, inverse,
                  is_solved, cost, allowed_after, random_scramble, parse)
from cube.cube import stickers

U, R, F, D, L, B = range(6)          # colours = face indices of the solved cube


def face(state, f):
    return list(state[9 * f: 9 * f + 9])


# basic structure

def test_54_distinct_stickers():
    assert len(set(stickers)) == 54


def test_solved_state():
    assert is_solved(solved) and cost(solved) == 0
    assert len(move_names) == 18


# algebraic identities

@pytest.mark.parametrize("f", "UDFBLR")
def test_quarter_turn_has_order_4(f):
    s = SOLVED
    for k in range(1, 5):
        s = apply_move(s, f)
        assert is_solved(s) == (k == 4)


@pytest.mark.parametrize("m", move_names)
def test_move_then_inverse(m):
    assert is_solved(apply_sequence(solved, [m, inverse(m)]))


@pytest.mark.parametrize("f", "UDFBLR")
def test_half_turn_is_two_quarters(f):
    assert apply_move(solved, f + "2") == apply_sequence(solved, f"{f} {f}")
    assert apply_move(solved, f + "'") == apply_sequence(solved, f"{f} {f} {f}")


def test_sexy_move_has_order_6():
    s = solved
    for k in range(1, 7):
        s = apply_sequence(s, "R U R' U'")
        assert is_solved(s) == (k == 6)


def test_opposite_faces_commute():
    for a, b in ("UD", "FB", "LR"):
        assert apply_sequence(solved, f"{a} {b}") == apply_sequence(solved, f"{b} {a}")


def test_adjacent_faces_do_not_commute():
    assert apply_sequence(solved, "R U") != apply_sequence(solved, "U R")


@pytest.mark.parametrize("seed", range(20))
def test_scramble_then_inverse(seed):
    s = random_scramble(25, seed)
    assert is_solved(apply_sequence(apply_sequence(solved, s), inverse(s)))


# geometry: the moves turn the right way 

def test_R_brings_front_up():
    s = apply_move(solved, "R")
    assert [face(s, U)[i] for i in (2, 5, 8)] == [F, F, F]
    assert [face(s, F)[i] for i in (2, 5, 8)] == [D, D, D]


def test_U_brings_right_to_front():
    s = apply_move(solved, "U")
    assert face(s, F)[:3] == [R, R, R]
    assert face(s, L)[:3] == [F, F, F]


def test_F_brings_left_to_up():
    s = apply_move(solved, "F")
    assert face(s, U)[6:] == [L, L, L]


# cost function

@pytest.mark.parametrize("m", move_names)
def test_one_move_changes_at_most_20_stickers(m):
    # quarter and half turns both move exactly 20 non-centre stickers
    # (this proves the heuristic h1 = ceil(cost / 20) is admissible)
    labelled = bytes(range(54))              # every sticker has its own label
    moved = sum(a != b for a, b in zip(labelled, apply_move(labelled, m)))
    assert moved == 20


def test_cost_of_one_quarter_turn():
    # the 8 stickers on the turned face keep their colour; 12 side stickers change
    assert cost(apply_move(solved, "R")) == 12


def test_superflip_cost_is_24():
    superflip = "U R2 F B R B2 R U2 L B2 R U' D' R2 F R' L B2 U2 F2"
    s = apply_sequence(solved, superflip)
    assert cost(s) == 24                      # every edge flipped, corners solved
    assert all(face(s, f)[4] == f for f in range(6))


# --- the graph: exact BFS layer sizes (known values, half-turn metric) -----

def test_bfs_layer_counts_up_to_depth_4():
    known = [1, 18, 243, 3240, 43239]
    seen = {solved}
    frontier = [solved]
    counts = [1]
    for _ in range(4):
        nxt = []
        for s in frontier:
            for m in move_names:
                t = apply_move(s, m)
                if t not in seen:
                    seen.add(t)
                    nxt.append(t)
        frontier = nxt
        counts.append(len(nxt))
    assert counts == known


def test_pruning_counts():
    # canonical sequences: 18, 243, 3240 (pruned tree has no duplicates up to depth 3)
    layer = [None]
    sizes = []
    for _ in range(3):
        layer = [m for last in layer for m in allowed_after(last)]
        sizes.append(len(layer))
    assert sizes == [18, 18 * 15 - 27, 3240]


def test_parse_rejects_bad_moves():
    with pytest.raises(ValueError):
        parse("R X2")
