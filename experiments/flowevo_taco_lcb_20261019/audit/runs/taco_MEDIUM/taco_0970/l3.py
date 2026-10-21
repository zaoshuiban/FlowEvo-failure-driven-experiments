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

    # Build the multiset of all possible tap counts.
    # For tap r, there is one slot on every key whose capacity is at least r.
    costs = []
    max_size = max(key_sizes)
    for tap in range(1, max_size + 1):
        cnt = sum(1 for size in key_sizes if size >= tap)
        costs.extend([tap] * cnt)

    # costs is already sorted in increasing order.
    # Assign largest frequencies to smallest tap counts.
    answer = 0
    for i in range(n):
        answer += frequencies[i] * costs[i]

    print(answer)


if __name__ == "__main__":
    solve()