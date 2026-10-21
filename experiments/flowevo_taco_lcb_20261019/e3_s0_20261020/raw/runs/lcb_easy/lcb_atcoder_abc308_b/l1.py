import sys

def main():
    tokens = sys.stdin.read().split()
    it = iter(tokens)

    N = int(next(it))
    M = int(next(it))

    C = [next(it) for _ in range(N)]
    D = [next(it) for _ in range(M)]

    P = [int(next(it)) for _ in range(M + 1)]

    price = {D[i]: P[i + 1] for i in range(M)}

    answer = sum(price.get(color, P[0]) for color in C)

    print(answer)

if __name__ == "__main__":
    main()