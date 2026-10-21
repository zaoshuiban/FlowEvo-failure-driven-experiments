import sys

MOD = 1_000_000_007


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    risk = [0] + data[idx:idx + n]
    idx += n

    k = data[idx] if idx < len(data) else 0
    idx += 1

    graph = [[] for _ in range(n + 1)]

    for _ in range(k):
        a = data[idx]
        b = data[idx + 1]
        idx += 2

        graph[a].append(b)
        graph[b].append(a)

    visited = [False] * (n + 1)
    answer = 1

    for start in range(1, n + 1):
        if visited[start]:
            continue

        stack = [start]
        visited[start] = True

        min_cost = 10**18
        min_count = 0

        while stack:
            city = stack.pop()
            cost = risk[city]

            if cost < min_cost:
                min_cost = cost
                min_count = 1
            elif cost == min_cost:
                min_count += 1

            for nxt in graph[city]:
                if not visited[nxt]:
                    visited[nxt] = True
                    stack.append(nxt)

        if min_cost == 0:
            ways = (pow(2, min_count, MOD) - 1) % MOD
        else:
            ways = min_count % MOD

        answer = (answer * ways) % MOD

    print(answer)


if __name__ == "__main__":
    solve()