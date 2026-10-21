import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N = data[0]
    A = [0] + data[1:1 + N]

    seen = [-1] * (N + 1)
    path = []

    v = 1
    while seen[v] == -1:
        seen[v] = len(path)
        path.append(v)
        v = A[v]

    start = seen[v]
    cycle = path[start:]

    print(len(cycle))
    print(*cycle)

if __name__ == "__main__":
    main()