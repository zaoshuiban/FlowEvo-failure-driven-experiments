import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, x1, x2 = data[0], data[1], data[2]
    c = data[3:3 + n]

    servers = [(c[i], i + 1) for i in range(n)]
    servers.sort(key=lambda p: p[0], reverse=True)

    def attempt(xa: int, xb: int):
        kA = 0
        for i in range(n):
            k = i + 1
            if servers[i][0] * k >= xa:
                kA = k
                break

        if kA == 0:
            return None

        for q in range(1, n - kA + 1):
            pos = kA + q - 1
            if servers[pos][0] * q >= xb:
                group_a = [servers[i][1] for i in range(kA)]
                group_b = [servers[i][1] for i in range(kA, kA + q)]
                return kA, group_a, q, group_b

        return None

    result = attempt(x1, x2)

    if result is not None:
        k1, group1, k2, group2 = result
        answer = [
            "Yes",
            f"{k1} {k2}",
            " ".join(map(str, group1)),
            " ".join(map(str, group2)),
        ]
    else:
        result = attempt(x2, x1)

        if result is not None:
            ka, group_a, kb, group_b = result

            k1, group1 = kb, group_b
            k2, group2 = ka, group_a

            answer = [
                "Yes",
                f"{k1} {k2}",
                " ".join(map(str, group1)),
                " ".join(map(str, group2)),
            ]
        else:
            answer = ["No"]

    sys.stdout.write("\n".join(answer))


if __name__ == "__main__":
    solve()