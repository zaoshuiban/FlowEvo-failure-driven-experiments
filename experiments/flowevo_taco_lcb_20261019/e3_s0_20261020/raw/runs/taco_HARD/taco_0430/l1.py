import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, K = data[0], data[1]
    A = data[2:2 + n]

    M = max(A)

    if K == 0:
        Dmax = M
        start = 1
    else:
        Dmax = M - K
        if Dmax < 0:
            Dmax = 0
        start = K + 1

    divisors = [[] for _ in range(Dmax + 1)]
    if start <= Dmax:
        for d in range(start, Dmax + 1):
            for multiple in range(d, Dmax + 1, d):
                divisors[multiple].append(d)

    best = [0] * (M + 1)
    bad_left = 0
    answer = 0

    if K == 0:
        for idx, x in enumerate(A, 1):
            previous = best[x]
            if previous > bad_left:
                bad_left = previous

            answer += idx - bad_left

            for d in divisors[x]:
                best[d] = idx
    else:
        last_k = 0

        for idx, x in enumerate(A, 1):
            if x > K:
                candidate = last_k
                if best[x] > candidate:
                    candidate = best[x]
                if candidate > bad_left:
                    bad_left = candidate

            answer += idx - bad_left

            if x == K:
                last_k = idx
            elif x > K:
                value = x - K
                for d in divisors[value]:
                    best[d] = idx

    print(answer)


if __name__ == "__main__":
    solve()