import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    ptr = 0

    n = data[ptr]
    ptr += 1

    values = []
    counts = []

    for _ in range(n):
        ci = data[ptr]
        ptr += 1
        counts.append(ci)
        values.append(data[ptr:ptr + ci])
        ptr += ci

    m = data[ptr]
    ptr += 1

    max_indices = [counts[i] - 1 for i in range(n)]
    best_possible = tuple(max_indices)

    banned = set()
    banned_builds = []

    for _ in range(m):
        build = [data[ptr + i] - 1 for i in range(n)]
        ptr += n
        build_tuple = tuple(build)

        strength = 0
        for i in range(n):
            strength += values[i][build_tuple[i]]

        banned.add(build_tuple)
        banned_builds.append((build_tuple, strength))

    if best_possible not in banned:
        print(" ".join(str(x + 1) for x in best_possible))
        return

    best_strength = -1
    best_build = None

    for build, strength in banned_builds:
        for i in range(n):
            if build[i] > 0:
                candidate_strength = (
                    strength
                    - values[i][build[i]]
                    + values[i][build[i] - 1]
                )

                if candidate_strength > best_strength:
                    candidate = list(build)
                    candidate[i] -= 1
                    candidate = tuple(candidate)

                    if candidate not in banned:
                        best_strength = candidate_strength
                        best_build = candidate

    print(" ".join(str(x + 1) for x in best_build))


if __name__ == "__main__":
    solve()