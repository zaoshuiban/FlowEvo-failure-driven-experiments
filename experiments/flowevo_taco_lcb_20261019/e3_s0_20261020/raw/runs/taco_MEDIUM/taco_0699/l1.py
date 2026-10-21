import sys


def solve() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    T = int(data[0])
    idx = 1
    answers = []

    for _ in range(T):
        n = int(data[idx])
        idx += 1
        t = data[idx]
        idx += 1

        mapping = [-1] * 26
        used_image = [False] * 26
        assigned_count = 0

        result = bytearray()

        for b in t:
            c = b - ord('a')
            y = mapping[c]

            if y == -1:
                if assigned_count == 25:
                    for candidate in range(26):
                        if not used_image[candidate]:
                            y = candidate
                            break
                else:
                    for candidate in range(26):
                        if used_image[candidate]:
                            continue

                        cur = candidate
                        creates_cycle = False

                        while True:
                            if cur == c:
                                creates_cycle = True
                                break

                            nxt = mapping[cur]
                            if nxt == -1:
                                break

                            cur = nxt

                        if not creates_cycle:
                            y = candidate
                            break

                mapping[c] = y
                used_image[y] = True
                assigned_count += 1

            result.append(y + ord('a'))

        answers.append(result.decode())

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()