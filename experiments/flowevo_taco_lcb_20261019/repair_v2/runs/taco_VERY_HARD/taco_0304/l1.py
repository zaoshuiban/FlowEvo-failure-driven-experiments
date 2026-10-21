import sys

MOD = 10**9 + 7

def main():
    input = sys.stdin.readline
    n, k = map(int, input().split())
    adj = [[] for _ in range(n + 1)]

    for _ in range(n - 1):
        u, v = map(int, input().split())
        adj[u].append(v)
        adj[v].append(u)

    INF = k + 1

    def dfs(u, parent):
        # State: (a, b)
        # a = distance from u to the nearest black vertex in the processed component,
        #     capped at INF if it is > k or absent.
        # b = maximum distance from u to an uncovered vertex in the component,
        #     or -1 if all vertices are already covered.
        dp = {(0, -1): 1, (INF, 0): 1}
        # u is black, u is white

        for v in adj[u]:
            if v == parent:
                continue

            child_dp = dfs(v, u)

            transformed = []
            for (c, bv), cnt in child_dp.items():
                if c == INF:
                    new_c = INF
                else:
                    new_c = c + 1
                    if new_c > k:
                        new_c = INF

                if bv == -1:
                    new_b = -1
                else:
                    new_b = bv + 1
                    if new_b > k:
                        continue

                transformed.append((new_c, new_b, cnt))

            ndp = {}

            for (a, b), cnt1 in dp.items():
                for new_c, new_b, cnt2 in transformed:
                    new_a = min(a, new_c)

                    rem_a = b
                    if b != -1 and new_c != INF and b + new_c <= k:
                        rem_a = -1

                    rem_b = new_b
                    if new_b != -1 and a != INF and new_b + a <= k:
                        rem_b = -1

                    new_rem = max(rem_a, rem_b)

                    key = (new_a, new_rem)
                    ndp[key] = (ndp.get(key, 0) + cnt1 * cnt2) % MOD

            dp = ndp

        return dp

    root_dp = dfs(1, 0)

    answer = 0
    for (_, b), cnt in root_dp.items():
        if b == -1:
            answer = (answer + cnt) % MOD

    print(answer)


if __name__ == "__main__":
    main()