import sys


def solve() -> None:
    data = sys.stdin.readline().split()
    if not data:
        return
    n = int(data[0])
    mod = int(data[1])

    if mod == 1:
        print(0)
        return

    # F stores the inversion count distribution for permutations of current length.
    # Initially it is for length 0.
    F = [1]

    # A is the answer for permutations of length (current_length - 1).
    A = 0

    for length in range(1, n + 1):
        max_inv = len(F) - 1

        suffix = [0] * (max_inv + 2)
        for i in range(max_inv, -1, -1):
            suffix[i] = (suffix[i + 1] + F[i]) % mod

        cross = 0

        for d in range(1, length):
            h = 0
            limit = max_inv - d

            for b in range(limit):
                idx = b + d + 1
                h = (h + F[b] * suffix[idx]) % mod

            cross = (cross + (length - d) * h) % mod

        A = (length * A + cross) % mod

        if length < n:
            new_max_inv = max_inv + length - 1
            new_F = [0] * (new_max_inv + 1)

            window = 0
            for s in range(new_max_inv + 1):
                if s <= max_inv:
                    window += F[s]

                rem = s - length
                if 0 <= rem <= max_inv:
                    window -= F[rem]

                window %= mod
                new_F[s] = window

            F = new_F

    print(A % mod)


if __name__ == "__main__":
    solve()