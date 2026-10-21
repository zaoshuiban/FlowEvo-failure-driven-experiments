import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    idx = 0
    N = int(data[idx])
    idx += 1
    S = data[idx]
    idx += 1

    C = list(map(int, data[idx:idx + 26]))
    idx += 26

    K = int(data[idx])
    idx += 1

    base_always = 0
    suffixes = []
    n = len(S)

    for _ in range(K):
        P = data[idx]
        idx += 1
        m = len(P)

        lim = min(n, m)
        i = 0
        while i < lim and S[i] == P[i]:
            i += 1

        if i < lim:
            # First difference is inside S.
            if S[i] > P[i]:
                base_always += 1
        else:
            # One string is a prefix of the other.
            if m < n:
                # P is a proper prefix of S, so S + anything > P.
                base_always += 1
            elif m == n:
                # P == S. This depends on whether U is non-empty.
                suffixes.append(b'')
            else:
                # S is a proper prefix of P.
                suffixes.append(P[n:])

    M = len(suffixes)

    # Build a trie of all suffixes V such that P = S + V.
    children = [{}]
    terminal = [0]

    for s in suffixes:
        u = 0
        for ch in s:
            d = ch - 97
            nxt = children[u].get(d)
            if nxt is None:
                nxt = len(children)
                children[u][d] = nxt
                children.append({})
                terminal.append(0)
            u = nxt
        terminal[u] += 1

    nodes = len(children)

    # subtree_count[u] = number of suffix strings having prefix represented by u.
    subtree_count = [0] * nodes
    for u in range(nodes - 1, -1, -1):
        total = terminal[u]
        for v in children[u].values():
            total += subtree_count[v]
        subtree_count[u] = total

    possible_rank = [False] * (M + 1)
    used = [0] * 26

    sys.setrecursionlimit(1_000_000)

    def dfs(u: int, base_rank: int) -> None:
        """
        u          : current trie node
        base_rank  : number of suffixes strictly smaller than current prefix
        """
        possible_rank[base_rank] = True

        term_u = terminal[u]
        acc = 0  # sum of subtree counts for children with character < current d

        child_map = children[u]

        for d in range(26):
            # Rank if we stop immediately after appending character d.
            rank_after_char = base_rank + term_u + acc
            child = child_map.get(d)

            if used[d] < C[d]:
                possible_rank[rank_after_char] = True

                if child is not None:
                    used[d] += 1
                    dfs(child, rank_after_char)
                    used[d] -= 1

            if child is not None:
                acc += subtree_count[child]

    dfs(0, 0)

    ans = []
    for X in range(K + 1):
        need = X - base_always
        if 0 <= need <= M and possible_rank[need]:
            ans.append("Yes\n")
        else:
            ans.append("No\n")

    sys.stdout.write(''.join(ans))


if __name__ == "__main__":
    solve()