import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    X = data[1:1 + N]

    a1 = X[0]

    odd_gaps = []
    even_gaps = []
    odd_weights = []
    even_weights = []

    for k in range(1, N):
        gap = X[k] - X[k - 1]
        weight = N - k

        if k % 2 == 1:
            odd_gaps.append(gap)
            odd_weights.append(weight)
        else:
            even_gaps.append(gap)
            even_weights.append(weight)

    odd_gaps.sort()
    odd_weights.sort(reverse=True)
    even_gaps.sort()
    even_weights.sort(reverse=True)

    cost = sum(g * w for g, w in zip(odd_gaps, odd_weights))
    cost += sum(g * w for g, w in zip(even_gaps, even_weights))

    answer = N * a1 + cost
    print(answer)

if __name__ == "__main__":
    solve()