import sys
import os
import random


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, Q = data[0], data[1]

    seed = int.from_bytes(os.urandom(16), "little")
    rng = random.Random(seed)

    hash_value = [0] * (N + 1)
    for i in range(1, N + 1):
        hash_value[i] = rng.getrandbits(128)

    mask = (1 << 128) - 1

    pref_a = [0] * (N + 1)
    pref_b = [0] * (N + 1)

    idx = 2

    cur = 0
    for i in range(1, N + 1):
        cur = (cur + hash_value[data[idx]]) & mask
        pref_a[i] = cur
        idx += 1

    cur = 0
    for i in range(1, N + 1):
        cur = (cur + hash_value[data[idx]]) & mask
        pref_b[i] = cur
        idx += 1

    answers = []

    for _ in range(Q):
        l = data[idx]
        r = data[idx + 1]
        L = data[idx + 2]
        R = data[idx + 3]
        idx += 4

        if r - l != R - L:
            answers.append("No\n")
            continue

        hash_a = (pref_a[r] - pref_a[l - 1]) & mask
        hash_b = (pref_b[R] - pref_b[L - 1]) & mask

        answers.append("Yes\n" if hash_a == hash_b else "No\n")

    sys.stdout.write("".join(answers))


if __name__ == "__main__":
    solve()