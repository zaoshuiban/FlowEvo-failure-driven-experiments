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
        idx += 1

        a = data[idx:idx + n]
        idx += n

        b = data[idx:idx + n]
        idx += n

        ans = 0

        # Bits up to 30 are checked for safety; under the given constraints,
        # bit 30 will simply never be possible.
        for bit in range(30, -1, -1):
            candidate = ans | (1 << bit)

            freq = {}
            for x in a:
                value = x & candidate
                freq[value] = freq.get(value, 0) + 1

            possible = True
            for x in b:
                need = (x & candidate) ^ candidate
                count = freq.get(need, 0)

                if count == 0:
                    possible = False
                    break

                if count == 1:
                    del freq[need]
                else:
                    freq[need] = count - 1

            if possible:
                ans = candidate

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers) + "\n")


if __name__ == "__main__":
    solve()