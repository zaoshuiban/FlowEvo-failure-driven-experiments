import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    qr = [(next(it), next(it)) for _ in range(N)]

    Q = next(it)
    answers = []

    for _ in range(Q):
        t = next(it) - 1
        d = next(it)

        q, r = qr[t]
        answers.append(str(d + (r - d % q) % q))

    print("\n".join(answers))

if __name__ == "__main__":
    main()