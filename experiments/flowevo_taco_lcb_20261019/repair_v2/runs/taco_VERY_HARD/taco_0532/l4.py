import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        d = data[idx + 1]
        idx += 2

        buckets = [[] for _ in range(d)]
        possible = True

        end = idx + n
        residue = 0

        while idx < end:
            value = data[idx] - 1  # convert to 0-based value

            if value % d != residue:
                possible = False
                idx = end
                break

            buckets[residue].append(value // d)

            idx += 1
            residue += 1
            if residue == d:
                residue = 0

        if not possible:
            answers.append("-1")
            continue

        total_swaps = 0

        for arr in buckets:
            k = len(arr)
            if k <= 1:
                continue

            bit = [0] * (k + 1)
            inversions = 0
            seen = 0

            for x in arr:
                # Count already seen values <= x
                count_le = 0
                pos = x + 1
                while pos > 0:
                    count_le += bit[pos]
                    pos -= pos & -pos

                inversions += seen - count_le

                pos = x + 1
                while pos <= k:
                    bit[pos] += 1
                    pos += pos & -pos

                seen += 1

            total_swaps += inversions

        answers.append(str(total_swaps))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()