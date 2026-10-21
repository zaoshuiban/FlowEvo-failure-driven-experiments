import sys
import itertools

numbers = [4, 8, 15, 16, 23, 42]

def ask(i, j):
    print(f"? {i} {j}", flush=True)
    return int(sys.stdin.readline())

p12 = ask(1, 2)
p23 = ask(2, 3)
p34 = ask(3, 4)
p45 = ask(4, 5)

for perm in itertools.permutations(numbers):
    if (
        perm[0] * perm[1] == p12 and
        perm[1] * perm[2] == p23 and
        perm[2] * perm[3] == p34 and
        perm[3] * perm[4] == p45
    ):
        print("! " + " ".join(map(str, perm)), flush=True)
        break