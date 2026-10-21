import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    A = [next(it) for _ in range(N)]

    M = next(it)
    B = [next(it) for _ in range(M)]

    L = next(it)
    C = [next(it) for _ in range(L)]

    Q = next(it)
    X = [next(it) for _ in range(Q)]

    ab = {a + b for a in A for b in B}
    possible = {s + c for s in ab for c in C}

    ans = ["Yes" if x in possible else "No" for x in X]
    sys.stdout.write("\n".join(ans))

if __name__ == "__main__":
    main()