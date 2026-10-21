import sys


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    m = int(data[1])
    c = int(data[2])
    idx = 3

    bit = [0] * (n + 2)
    answers = []

    for _ in range(m):
        cmd = data[idx]
        idx += 1

        if cmd[0] == 83:  # 'S'
            u = int(data[idx])
            v = int(data[idx + 1])
            k = int(data[idx + 2])
            idx += 3

            if k != 0:
                i = u
                while i <= n:
                    bit[i] += k
                    i += i & -i

                i = v + 1
                while i <= n:
                    bit[i] -= k
                    i += i & -i

        else:  # 'Q'
            p = int(data[idx])
            idx += 1

            total = 0
            i = p
            while i > 0:
                total += bit[i]
                i -= i & -i

            answers.append(str(total + c))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()