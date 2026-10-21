import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = [0] + data[1:1 + n]

    seen = [-1] * (n + 1)
    path = []

    v = 1
    while seen[v] == -1:
        seen[v] = len(path)
        path.append(v)
        v = a[v]

    cycle = path[seen[v]:]

    sys.stdout.write(str(len(cycle)) + "\n")
    sys.stdout.write(" ".join(map(str, cycle)) + "\n")


if __name__ == "__main__":
    main()