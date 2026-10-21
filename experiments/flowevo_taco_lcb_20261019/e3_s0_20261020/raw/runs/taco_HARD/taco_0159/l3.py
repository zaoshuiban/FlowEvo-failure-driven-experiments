import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    cnt = [0, 0, 0, 0]

    idx = 1
    for _ in range(n):
        x = data[idx]
        y = data[idx + 1]
        idx += 2

        # Since x and y are even, use their parity after dividing by 2.
        px = (x // 2) & 1
        py = (y // 2) & 1
        cnt[px * 2 + py] += 1

    # Interesting triangles are exactly those where at least two vertices
    # have the same parity class among the four classes above.
    answer = 0

    # All three vertices in the same parity class.
    for c in cnt:
        if c >= 3:
            answer += c * (c - 1) * (c - 2) // 6

    # Exactly two vertices in one parity class and the third outside it.
    for c in cnt:
        if c >= 2:
            answer += (c * (c - 1) // 2) * (n - c)

    print(answer)


if __name__ == "__main__":
    solve()