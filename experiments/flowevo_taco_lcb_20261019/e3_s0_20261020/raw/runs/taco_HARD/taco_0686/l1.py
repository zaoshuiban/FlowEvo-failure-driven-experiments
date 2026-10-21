import sys

def solve() -> None:
    tokens = sys.stdin.buffer.read().split()
    it = iter(tokens)

    t = int(next(it))
    answers = []

    for _ in range(t):
        n = int(next(it))
        perm = [0] * n

        for i in range(n):
            row = next(it)
            perm[i] = row.find(b'1')

        ans = 0

        for left in range(n):
            mn = n
            mx = -1

            for right in range(left, n):
                value = perm[right]

                if value < mn:
                    mn = value
                if value > mx:
                    mx = value

                if mx - mn == right - left:
                    ans += 1

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()