import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    p = data[1:1 + n]

    # Count inversions using a Fenwick tree.
    bit = [0] * (n + 2)

    def add(i: int) -> None:
        while i <= n:
            bit[i] += 1
            i += i & -i

    def query(i: int) -> int:
        s = 0
        while i > 0:
            s += bit[i]
            i -= i & -i
        return s

    inversions = 0
    for i, x in enumerate(p):
        # Previous elements greater than x.
        inversions += i - query(x)
        add(x)

    answer = 2 * inversions - (inversions & 1)
    print(f"{answer:.10f}")


if __name__ == "__main__":
    main()