import sys
from array import array


def main():
    input = sys.stdin.buffer.readline
    n, m, c = map(int, input().split())

    bit = array('q', [0]) * (n + 2)
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
            neg_k = -k
            while i <= n:
                bit[i] += neg_k
                i += i & -i

        else:
            p = int(parts[1])

            total = 0
            i = p
            while i > 0:
                total += bit[i]
                i -= i & -i

            answers.append(str(c + total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()