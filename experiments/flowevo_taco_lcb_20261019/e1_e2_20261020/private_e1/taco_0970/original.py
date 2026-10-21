import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    frequencies = data[idx:idx + n]
    idx += n

    k = data[idx]
    idx += 1

    key_sizes = data[idx:idx + k]

    if sum(key_sizes) < n:
        print(-1)
        return

    frequencies.sort(reverse=True)

    answer = 0
    assigned = 0

    max_key_size = max(key_sizes)

    for taps in range(1, max_key_size + 1):
        for size in key_sizes:
            if size >= taps:
                if assigned == n:
                    break
                answer += frequencies[assigned] * taps
                assigned += 1
        if assigned == n:
            break

    print(answer)


if __name__ == "__main__":
    solve()