import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    adj = [[] for _ in range(n)]

    idx = 2
    for _ in range(m):
        a = data[idx] - 1
        b = data[idx + 1] - 1
        idx += 2
        adj[a].append(b)
        adj[b].append(a)

    color = [-1] * n
    odd_cycles = 0

    for start in range(n):
        if color[start] != -1:
            continue

        color[start] = 0
        stack = [start]
        bad = False

        while stack:
            v = stack.pop()

            for to in adj[v]:
                if color[to] == -1:
                    color[to] = color[v] ^ 1
                    stack.append(to)
                elif color[to] == color[v]:
                    bad = True

        if bad:
            odd_cycles += 1

    answer = odd_cycles
    if (n - answer) % 2 == 1:
        answer += 1

    print(answer)

if __name__ == "__main__":
    main()