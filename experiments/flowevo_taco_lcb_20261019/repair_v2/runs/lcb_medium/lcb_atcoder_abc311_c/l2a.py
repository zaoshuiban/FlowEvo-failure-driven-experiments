import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = [x - 1 for x in data[1:1 + n]]

    pos = [-1] * n
    path = []

    v = 0
    while pos[v] == -1:
        pos[v] = len(path)
        path.append(v)
        v = a[v]

    cycle = path[pos[v]:]

    print(len(cycle))
    print(*[x + 1 for x in cycle])

if __name__ == "__main__":
    main()