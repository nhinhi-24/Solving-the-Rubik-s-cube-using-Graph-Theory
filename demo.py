from cube import SOLVED, apply_sequence, inverse, is_solved, cost, random_scramble, to_string

scramble = random_scramble(10, seed=2026)
state = apply_sequence(SOLVED, scramble)

print("Scramble:", scramble)
print(to_string(state))
print("cost (wrong stickers) =", cost(state))

undo = inverse(scramble)
print("Inverse :", undo)
print("Solved again:", is_solved(apply_sequence(state, undo)))
