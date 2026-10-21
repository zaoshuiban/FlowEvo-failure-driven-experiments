import sys
import heapq


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []
    INF = 10**30

    for _ in range(t):
        n = data[idx]
        m = data[idx + 1]
        k = data[idx + 2]
        idx += 3

        target = n + m
        batteries = []

        for _ in range(k):
            x = data[idx]
            y = data[idx + 1]
            cost = data[idx + 2]
            energy = data[idx + 3]
            idx += 4

            pos = x + y
            reach = pos + energy
            batteries.append((pos, cost, reach))

        batteries.sort(key=lambda b: b[0])

        # Heap entries: (minimum cost to get this state, maximum reachable x+y)
        # Initially at (0, 0) with energy 0.
        heap = [(0, 0)]
        answer = INF

        for pos, cost, reach in batteries:
            # Remove states that cannot reach this battery's position.
            while heap and heap[0][1] < pos:
                heapq.heappop(heap)

            if not heap:
                break

            best_cost_to_reach_here = heap[0][0]
            new_cost = best_cost_to_reach_here + cost

            if reach >= target:
                answer = min(answer, new_cost)

            heapq.heappush(heap, (new_cost, reach))

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()