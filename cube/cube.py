"""
3x3x3 Rubik's cube: facelet model, 18 moves (half-turn metric), cost function.

STATE
    A state is a `bytes` object of length 54. state[i] is the colour (0..5) of
    sticker i. `bytes` is immutable and hashable, so states can go straight
    into sets and dicts (BFS visited sets, the paper's HashMap, ...).

STICKER NUMBERING (Kociemba order U, R, F, D, L, B; 9 stickers per face)
    Each face is read row by row as you look straight at it, with this net:

                  U0 U1 U2
                  U3 U4 U5
                  U6 U7 U8
        L0 L1 L2  F0 F1 F2  R0 R1 R2  B0 B1 B2
        L3 L4 L5  F3 F4 F5  R3 R4 R5  B3 B4 B5
        L6 L7 L8  F6 F7 F8  R6 R7 R8  B6 B7 B8
                  D0 D1 D2
                  D3 D4 D5
                  D6 D7 D8

    Index = 9 * face_index + position, with U=0, R=1, F=2, D=3, L=4, B=5.
    So U0..U8 = 0..8, R0..R8 = 9..17, F = 18..26, D = 27..35, L = 36..44,
    B = 45..53. The centre of each face (position 4) never moves.

MOVES
    18 moves: U U2 U' D D2 D' F F2 F' B B2 B' L L2 L' R R2 R'.
    "X"  = 90 degrees clockwise when looking at face X,
    "X2" = 180 degrees, "X'" = 90 degrees anticlockwise.
    Internally every move is a permutation P of 0..53:
        new_state[j] = state[P[j]].
    The permutations are computed from 3-D geometry (not typed by hand), which
    removes the usual source of bugs.
"""

from __future__ import annotations

import random
from operator import itemgetter

FACES = "URFDLB"                     # face order used for sticker numbering
COLOUR_NAMES = "WRGYOB"              # U white, R red, F green, D yellow, L orange, B blue

# Outward normal of each face (x to the right, y up, z towards the viewer).
NORMAL = {
    "U": (0, 1, 0), "D": (0, -1, 0),
    "R": (1, 0, 0), "L": (-1, 0, 0),
    "F": (0, 0, 1), "B": (0, 0, -1),
}

# For reading each face: (row direction, column direction). Row 0 is at the
# "top" of the face as drawn in the net above; column 0 at its left.
#   position p = 3*r + c,  sticker point = normal + (1-r)*up + (c-1)*right
_FACE_FRAME = {
    #       up vector    right vector
    "U": ((0, 0, -1), (1, 0, 0)),    # seen from above, F at the bottom
    "R": ((0, 1, 0), (0, 0, -1)),
    "F": ((0, 1, 0), (1, 0, 0)),
    "D": ((0, 0, 1), (1, 0, 0)),     # seen from below, F at the top
    "L": ((0, 1, 0), (0, 0, 1)),
    "B": ((0, 1, 0), (-1, 0, 0)),
}


def _add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def _scale(k, v):
    return tuple(k * c for c in v)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


# Each sticker = (cubie position, normal). Cubie position has coordinates in {-1,0,1}.
STICKERS: list[tuple[tuple[int, int, int], tuple[int, int, int]]] = []
for _f in FACES:
    _n = NORMAL[_f]
    _up, _right = _FACE_FRAME[_f]
    for _r in range(3):
        for _c in range(3):
            _pos = _add(_n, _scale(1 - _r, _up), _scale(_c - 1, _right))
            STICKERS.append((_pos, _n))

_INDEX = {s: i for i, s in enumerate(STICKERS)}


def _rotate_clockwise(v, n):
    """Rotate vector v by 90 degrees clockwise as seen looking at the face with
    outward normal n (= -90 degrees about n by the right-hand rule)."""
    # Rodrigues with theta = -90deg: v' = -(n x v) + n (n.v)
    return _add(_scale(-1, _cross(n, v)), _scale(_dot(n, v), n))


def _quarter_turn_perm(face: str) -> tuple[int, ...]:
    """Permutation P for a clockwise quarter turn: new[j] = old[P[j]]."""
    n = NORMAL[face]
    perm = list(range(54))
    for i, (pos, nor) in enumerate(STICKERS):
        if _dot(pos, n) == 1:                     # sticker is in the turning layer
            j = _INDEX[(_rotate_clockwise(pos, n), _rotate_clockwise(nor, n))]
            perm[j] = i                           # sticker i moves to place j
    return tuple(perm)


def _compose(p, q):
    """Permutation of doing p first, then q."""
    return tuple(p[q[j]] for j in range(54))


# ---------------------------------------------------------------------------
# The 18 moves
# ---------------------------------------------------------------------------

MOVE_NAMES: list[str] = []
MOVE_PERMS: dict[str, tuple[int, ...]] = {}
for _f in "UDFBLR":
    _p1 = _quarter_turn_perm(_f)
    _p2 = _compose(_p1, _p1)
    _p3 = _compose(_p2, _p1)
    for _suffix, _p in (("", _p1), ("2", _p2), ("'", _p3)):
        MOVE_NAMES.append(_f + _suffix)
        MOVE_PERMS[_f + _suffix] = _p

# itemgetter makes applying a move fast (C speed instead of a Python loop)
_GETTERS = {m: itemgetter(*p) for m, p in MOVE_PERMS.items()}

INVERSE_MOVE = {m: (m[0] if m.endswith("'") else m if m.endswith("2") else m + "'")
                for m in MOVE_NAMES}

OPPOSITE = {"U": "D", "D": "U", "F": "B", "B": "F", "L": "R", "R": "L"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def solved() -> bytes:
    """The solved cube."""
    return bytes(i // 9 for i in range(54))


SOLVED = solved()


def apply_move(state: bytes, move: str) -> bytes:
    """Return the state after one move, e.g. apply_move(s, "R'")."""
    return bytes(_GETTERS[move](state))


def parse(sequence: str | list[str]) -> list[str]:
    """'R U2 F'' -> ['R', 'U2', "F'"]. Also accepts a list, and the
    characters ’ and ′ for the prime."""
    if isinstance(sequence, list):
        moves = sequence
    else:
        moves = sequence.replace("’", "'").replace("′", "'").split()
    for m in moves:
        if m not in MOVE_PERMS:
            raise ValueError(f"unknown move {m!r}")
    return moves


def apply_sequence(state: bytes, sequence: str | list[str]) -> bytes:
    """Apply a whole sequence such as "R U2 F'"."""
    for m in parse(sequence):
        state = apply_move(state, m)
    return state


def inverse(sequence: str | list[str]) -> str:
    """Sequence that undoes `sequence`: reverse it and invert every move."""
    return " ".join(INVERSE_MOVE[m] for m in reversed(parse(sequence)))


def is_solved(state: bytes) -> bool:
    return state == SOLVED


def cost(state: bytes) -> int:
    """The paper's cost: number of stickers not in their solved colour (0..48)."""
    return sum(a != b for a, b in zip(state, SOLVED))


def allowed_after(last: str | None) -> list[str]:
    """Moves allowed after `last` with standard pruning:
    never the same face twice in a row, and opposite faces in a fixed order
    (U before D, F before B, L before R), because e.g. U D = D U.
    This removes duplicate paths but never loses a state."""
    if last is None:
        return MOVE_NAMES
    f = last[0]
    out = []
    for m in MOVE_NAMES:
        g = m[0]
        if g == f:
            continue
        if g == OPPOSITE[f] and "UFL".find(g) >= 0:   # g is the 'first' of its pair
            continue
        out.append(m)
    return out


def random_scramble(length: int, seed: int | None = None) -> str:
    """Random scramble with the same pruning rules as allowed_after."""
    rng = random.Random(seed)
    moves: list[str] = []
    last = None
    for _ in range(length):
        last = rng.choice(allowed_after(last))
        moves.append(last)
    return " ".join(moves)


def to_string(state: bytes) -> str:
    """Pretty-print the cube as a net (W R G Y O B letters)."""
    c = [COLOUR_NAMES[x] for x in state]

    def row(face, r):
        b = 9 * FACES.index(face) + 3 * r
        return " ".join(c[b:b + 3])

    lines = []
    for r in range(3):
        lines.append(" " * 8 + row("U", r))
    for r in range(3):
        lines.append("  ".join(row(f, r) for f in "LFRB"))
    for r in range(3):
        lines.append(" " * 8 + row("D", r))
    return "\n".join(lines)


if __name__ == "__main__":
    s = random_scramble(10, seed=2026)
    print("Scramble:", s)
    st = apply_sequence(SOLVED, s)
    print(to_string(st))
    print("cost =", cost(st))
    print("solved again after inverse:", is_solved(apply_sequence(st, inverse(s))))
