import sys

def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        idx += 2

        friend_masks = [0] * n

        for i in range(n):
            s = data[idx]
            idx += 1

            mask = 0
            for j, ch in enumerate(s):
                if ch == 49:  # ord('1')
                    mask |= (1 << j)

            friend_masks[i] = mask

        total_masks = 1 << k

        popcount = [0] * total_masks
        for mask in range(1, total_masks):
            popcount[mask] = popcount[mask >> 1] + (mask & 1)

        best = k

        for chosen in range(1, total_masks):
            if popcount[chosen] >= best:
                continue

            ok = True
            for fm in friend_masks:
                if (fm & chosen) == 0:
                    ok = False
                    break

            if ok:
                best = popcount[chosen]
                if best == 1:
                    break

        answers.append(str(best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()