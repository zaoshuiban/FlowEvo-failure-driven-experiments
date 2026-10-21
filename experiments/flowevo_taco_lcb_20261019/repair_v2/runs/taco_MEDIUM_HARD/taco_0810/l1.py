import sys


def solve():
    input = sys.stdin.buffer.readline

    n, m, c = map(int, input().split())
    bit = [0] * (n + 2)
    answers = []

    for _ in range(m):
        parts = input().split()

        if parts[0] == b'S':
            u = int(parts[1])
            v = int(parts[2])
            k = int(parts[3])

            i = u
            while i <= n:
                bit[i] += k
                i += i & -i

            i = v + 1
            while i <= n:
                bit[i] -= k
                i += i & -i

        else:
            p = int(parts[1])
            result = c

            i = p
            while i > 0:
                result += bit[i]
                i -= i & -i

            answers.append(str(result))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()