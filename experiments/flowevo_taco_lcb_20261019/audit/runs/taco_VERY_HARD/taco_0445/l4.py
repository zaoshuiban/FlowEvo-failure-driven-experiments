import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        idx += 1

        a = list(map(int, data[idx:idx + n]))
        idx += n

        s = data[idx]
        idx += 1

        blocks = []
        current_fixed = -1
        ok = True

        for i in range(n):
            if i == 0 or s[i - 1] != ord('='):
                if i > 0:
                    blocks.append(current_fixed)
                current_fixed = -1

            value = a[i]
            if value != -1:
                if current_fixed == -1:
                    current_fixed = value
                elif current_fixed != value:
                    ok = False

        blocks.append(current_fixed)

        if not ok:
            answers.append("NO")
            continue

        relations = s.replace(b'=', b'')
        m = len(blocks)

        left = [0] * m

        for i in range(m):
            base = 0 if blocks[i] == -1 else blocks[i]

            if i > 0 and relations[i - 1] == ord('<'):
                candidate = left[i - 1] + 1
                if candidate > base:
                    base = candidate

            left[i] = base

        right_next = 0

        for i in range(m - 1, -1, -1):
            base = 0 if blocks[i] == -1 else blocks[i]
            right = base

            if i + 1 < m and relations[i] == ord('>'):
                candidate = right_next + 1
                if candidate > right:
                    right = candidate

            final_value = left[i] if left[i] > right else right

            if blocks[i] != -1 and final_value != blocks[i]:
                ok = False
                break

            right_next = right

        answers.append("YES" if ok else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()