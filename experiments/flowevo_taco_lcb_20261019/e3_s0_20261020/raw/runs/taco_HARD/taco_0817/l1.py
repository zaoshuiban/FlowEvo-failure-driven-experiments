import sys


def main():
    input = sys.stdin.buffer.readline

    n_line = input()
    if not n_line:
        return
    n = int(n_line)

    MAXB = 10  # n <= 1000 < 2^10
    resp1 = [None] * MAXB
    resp0 = [None] * MAXB

    write = sys.stdout.write
    flush = sys.stdout.flush

    def ask(indices):
        write(str(len(indices)) + "\n")
        write(" ".join(map(str, indices)) + "\n")
        flush()

        arr = []
        while len(arr) < n:
            line = input()
            if not line:
                break
            arr.extend(map(int, line.split()))
        return arr[:n]

    for b in range(MAXB):
        ones = [i + 1 for i in range(n) if (i >> b) & 1]
        if not ones:
            continue

        zeros = [i + 1 for i in range(n) if ((i >> b) & 1) == 0]

        resp1[b] = ask(ones)
        if zeros:
            resp0[b] = ask(zeros)

    INF = 10**18
    ans = [INF] * n

    for b in range(MAXB):
        arr = resp1[b]
        if arr is not None:
            for i in range(n):
                if ((i >> b) & 1) == 0 and arr[i] < ans[i]:
                    ans[i] = arr[i]

        arr = resp0[b]
        if arr is not None:
            for i in range(n):
                if ((i >> b) & 1) == 1 and arr[i] < ans[i]:
                    ans[i] = arr[i]

    write("-1\n")
    write(" ".join(map(str, ans)) + "\n")
    flush()


if __name__ == "__main__":
    main()