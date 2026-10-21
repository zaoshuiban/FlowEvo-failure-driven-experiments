import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    ptr = 0
    n = data[ptr]
    ptr += 1

    slots = []
    for _ in range(n):
        c = data[ptr]
        ptr += 1
        slots.append(data[ptr:ptr + c])
        ptr += c

    m = data[ptr]
    ptr += 1

    banned = set()
    banned_builds = []

    for _ in range(m):
        build = tuple(data[ptr + i] - 1 for i in range(n))
        ptr += n
        banned.add(build)
        banned_builds.append(build)

    max_build = tuple(len(s) - 1 for s in slots)

    if max_build not in banned:
        print(" ".join(str(x + 1) for x in max_build))
        return

    best_strength = -1
    best_build = None

    for build in banned_builds:
        base_strength = sum(slots[i][build[i]] for i in range(n))

        for i in range(n):
            if build[i] > 0:
                candidate = list(build)
                candidate[i] -= 1
                candidate = tuple(candidate)

                if candidate not in banned:
                    strength = (
                        base_strength
                        - slots[i][build[i]]
                        + slots[i][build[i] - 1]
                    )

                    if strength > best_strength:
                        best_strength = strength
                        best_build = candidate

    print(" ".join(str(x + 1) for x in best_build))


if __name__ == "__main__":
    solve()