import sys

MOD = 998244353

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    it = iter(data)
    N = next(it)
    A = [0] + [next(it) for _ in range(N)]
    B = [0] + [next(it) for _ in range(N)]

    # P_i = first element of s_i, determined by A_i.
    P = [0] * (N + 1)
    invP = [0] * (N + 1)
    seen = [False] * (N + 1)

    for i in range(1, N + 1):
        x = (A[i] + 1) // 2  # ceil(A_i / 2)
        if x < 1 or x > N or seen[x]:
            print(0)
            return
        seen[x] = True
        P[i] = x
        invP[x] = i

    # Build forced edges phi(k) = i from specified B_i.
    out_to = [-1] * (N + 1)
    indeg = [0] * (N + 1)

    for i in range(1, N + 1):
        if B[i] == -1:
            continue

        bv = B[i]
        x = (bv + 1) // 2  # block of B_i
        if x < 1 or x > N:
            print(0)
            return

        k = invP[x]

        # In the same block, s_k and t_i must be on opposite sides,
        # hence their ranks have different parity.
        if (A[k] & 1) == (bv & 1):
            print(0)
            return

        if out_to[k] != -1 and out_to[k] != i:
            print(0)
            return

        if out_to[k] == -1:
            out_to[k] = i
            indeg[i] += 1

    visited = [False] * (N + 1)

    mono0 = 0
    mono1 = 0
    mixed = 0

    # Process path components.
    for v in range(1, N + 1):
        if visited[v] or indeg[v] != 0:
            continue

        cur = v
        has0 = False
        has1 = False

        while cur != -1 and not visited[cur]:
            visited[cur] = True
            if A[cur] & 1:
                has1 = True
            else:
                has0 = True
            cur = out_to[cur]

        if has0 and has1:
            mixed += 1
        elif has0:
            mono0 += 1
        elif has1:
            mono1 += 1

    # Remaining vertices form closed forced cycles.
    for v in range(1, N + 1):
        if visited[v]:
            continue

        cur = v
        has0 = False
        has1 = False

        while not visited[cur]:
            visited[cur] = True
            if A[cur] & 1:
                has1 = True
            else:
                has0 = True

            nxt = out_to[cur]
            if nxt == -1:
                print(0)
                return
            cur = nxt

        # Every cycle must contain both parities.
        if not (has0 and has1):
            print(0)
            return

    fact = [1] * (N + 1)
    for i in range(1, N + 1):
        fact[i] = fact[i - 1] * i % MOD

    M = mono0 + mono1 + mixed

    ans = fact[M]

    if mono0 > 0:
        ans -= mono0 * fact[M - 1]
    if mono1 > 0:
        ans -= mono1 * fact[M - 1]
    if mono0 > 0 and mono1 > 0:
        ans += mono0 * mono1 % MOD * fact[M - 2]

    ans %= MOD
    print(ans)


if __name__ == "__main__":
    solve()