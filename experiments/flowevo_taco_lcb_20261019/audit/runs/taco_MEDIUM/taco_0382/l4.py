import sys
from itertools import permutations

def solve():
    numbers = [4, 8, 15, 16, 23, 42]

    def ask(i, j):
        sys.stdout.write(f"? {i} {j}\n")
        sys.stdout.flush()
        return int(sys.stdin.buffer.readline())

    p12 = ask(1, 2)
    p13 = ask(1, 3)
    p14 = ask(1, 4)
    p15 = ask(1, 5)

    ans = None
    for perm in permutations(numbers):
        a = list(perm)
        if (a[0] * a[1] == p12 and
            a[0] * a[2] == p13 and
            a[0] * a[3] == p14 and
            a[0] * a[4] == p15):
            ans = a
            break

    sys.stdout.write("! " + " ".join(map(str, ans)) + "\n")
    sys.stdout.flush()

if __name__ == "__main__":
    solve()