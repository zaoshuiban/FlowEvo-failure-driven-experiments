import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    pos = 1
    answers = []

    for _ in range(t):
        n = int(data[pos])
        k = int(data[pos + 1])
        pos += 2

        friends = set()

        for _ in range(n):
            s = data[pos]
            pos += 1

            mask = 0
            for j, ch in enumerate(s):
                if ch == 49:  # ord('1')
                    mask |= 1 << j

            friends.add(mask)

        total_masks = 1 << k
        best = k + 1

        for chosen in range(1, total_masks):
            count = chosen.bit_count()

            if count >= best:
                continue

            ok = True
            for fm in friends:
                if (fm & chosen) == 0:
                    ok = False
                    break

            if ok:
                best = count

        # Since every friend likes at least one dish, choosing all dishes
        # always satisfies everyone. The fallback is just for safety.
        if best == k + 1:
            best = k

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()