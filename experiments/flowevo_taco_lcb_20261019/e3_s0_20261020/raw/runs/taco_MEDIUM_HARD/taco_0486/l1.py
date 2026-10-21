import sys


def process_computer(cur, tasks_by_computer, completed, remaining, graph, done):
    while True:
        progressed = False
        for v in tasks_by_computer[cur]:
            if not completed[v] and remaining[v] == 0:
                completed[v] = True
                done += 1
                progressed = True

                for nxt in graph[v]:
                    remaining[nxt] -= 1

        if not progressed:
            break

    return done


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1

    computer = [0] * (n + 1)
    tasks_by_computer = [[] for _ in range(4)]

    for i in range(1, n + 1):
        computer[i] = data[idx]
        idx += 1
        tasks_by_computer[computer[i]].append(i)

    graph = [[] for _ in range(n + 1)]
    remaining_initial = [0] * (n + 1)

    for i in range(1, n + 1):
        k = data[idx]
        idx += 1
        remaining_initial[i] = k

        for _ in range(k):
            prerequisite = data[idx]
            idx += 1
            graph[prerequisite].append(i)

    best_moves = 10**9

    for start in (1, 2, 3):
        completed = [False] * (n + 1)
        remaining = remaining_initial[:]
        done = 0
        moves = 0
        cur = start

        done = process_computer(
            cur, tasks_by_computer, completed, remaining, graph, done
        )

        while done < n:
            cur = cur % 3 + 1
            moves += 1
            done = process_computer(
                cur, tasks_by_computer, completed, remaining, graph, done
            )

        best_moves = min(best_moves, moves)

    print(n + best_moves)


if __name__ == "__main__":
    solve()