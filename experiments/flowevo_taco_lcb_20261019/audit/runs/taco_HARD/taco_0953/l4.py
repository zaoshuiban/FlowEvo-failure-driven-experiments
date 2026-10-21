import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    p = data[1:1 + n]

    # Count inversions using a Fenwick tree.
    bit = [0] * (n + 2)

    def add(idx: int) -> None:
        while idx <= n:
            bit[idx] += 1
            idx += idx & -idx

    def query(idx: int) -> int:
        result = 0
        while idx > 0:
            result += bit[idx]
            idx -= idx & -idx
        return result

    inversions = 0
    for i, x in enumerate(p):
        # Previous elements greater than x.
        inversions += i - query(x)
        add(x)

    answer = 2 * inversions - (inversions & 1)
    print(f"{answer:.10f}")


if __name__ == "__main__":
    main()