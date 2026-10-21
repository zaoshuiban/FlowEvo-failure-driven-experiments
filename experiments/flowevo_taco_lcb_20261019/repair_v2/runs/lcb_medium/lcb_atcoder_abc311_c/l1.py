import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    a = [x - 1 for x in data[1:1 + n]]

    state = [0] * n  # 0: unvisited, 1: visiting, 2: finished
    pos = [0] * n

    for start in range(n):
        if state[start] != 0:
            continue

        cur = start
        path = []

        while state[cur] == 0:
            state[cur] = 1
            pos[cur] = len(path)
            path.append(cur)
            cur = a[cur]

        if state[cur] == 1:
            idx = pos[cur]
            cycle = path[idx:]

            print(len(cycle))
            print(*[v + 1 for v in cycle])
            return

        for v in path:
            state[v] = 2

if __name__ == "__main__":
    main()