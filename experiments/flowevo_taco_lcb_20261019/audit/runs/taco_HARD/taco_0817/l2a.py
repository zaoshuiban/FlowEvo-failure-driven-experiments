import sys
import itertools


def solve() -> None:
    data = sys.stdin.buffer
    first = data.readline()
    if not first:
        return

    n = int(first)

    # Create n distinct 20-bit codes, all having exactly 10 ones.
    # Any two distinct such codes are incomparable: neither is a subset
    # of the other bitwise.
    codes = []
    for comb in itertools.combinations(range(20), 10):
        code = 0
        for bit in comb:
            code |= 1 << bit
        codes.append(code)
        if len(codes) == n:
            break

    INF = 10**18
    ans = [INF] * n
    out = sys.stdout

    for bit in range(20):
        query = [str(i + 1) for i, code in enumerate(codes) if (code >> bit) & 1]

        if not query:
            continue

        out.write(str(len(query)) + "\n")
        out.write(" ".join(query) + "\n")
        out.flush()

        response = []
        while len(response) < n:
            response.extend(map(int, data.readline().split()))

        for i, code in enumerate(codes):
            if ((code >> bit) & 1) == 0:
                if response[i] < ans[i]:
                    ans[i] = response[i]

    out.write("-1\n")
    out.write(" ".join(map(str, ans)) + "\n")
    out.flush()


if __name__ == "__main__":
    solve()