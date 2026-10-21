import sys

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    p = data[1:1 + n]

    inv = 0
    for i in range(n):
        pi = p[i]
        for j in range(i + 1, n):
            if pi > p[j]:
                inv += 1

    if inv % 2 == 0:
        ans = 2.0 * inv
    else:
        ans = 2.0 * inv - 1.0

    print(f"{ans:.10f}")

if __name__ == "__main__":
    main()