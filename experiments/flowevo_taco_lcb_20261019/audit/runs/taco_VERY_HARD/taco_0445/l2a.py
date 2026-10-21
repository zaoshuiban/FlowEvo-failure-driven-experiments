import sys


def solve():
    input = sys.stdin.buffer.readline

    line = input()
    while line and line.strip() == b'':
        line = input()
    if not line:
        return

    T = int(line)
    answers = []

    for _ in range(T):
        line = input()
        while line and line.strip() == b'':
            line = input()
        N = int(line)

        A = []
        while len(A) < N:
            A.extend(map(int, input().split()))

        S = input().strip()
        while S == b'':
            S = input().strip()

        fixed = [-1]
        rel = bytearray()
        comp = 0
        ok = True

        for i, value in enumerate(A):
            if value >= 0:
                if fixed[comp] == -1:
                    fixed[comp] = value
                elif fixed[comp] != value:
                    ok = False

            if i < N - 1:
                ch = S[i]
                if ch != ord('='):
                    rel.append(ch)
                    comp += 1
                    fixed.append(-1)

        if not ok:
            answers.append("NO")
            continue

        M = len(fixed)
        indegree = [0] * M

        for i, ch in enumerate(rel):
            if ch == ord('<'):
                indegree[i + 1] += 1
            else:  # '>'
                indegree[i] += 1

        lower = fixed[:]
        for i in range(M):
            if lower[i] == -1:
                lower[i] = 0

        queue = []
        for i in range(M):
            if indegree[i] == 0:
                queue.append(i)

        ptr = 0
        while ptr < len(queue):
            u = queue[ptr]
            ptr += 1

            next_value = lower[u] + 1

            if u > 0 and rel[u - 1] == ord('>'):
                v = u - 1
                if lower[v] < next_value:
                    lower[v] = next_value

                indegree[v] -= 1
                if indegree[v] == 0:
                    queue.append(v)

            if u < M - 1 and rel[u] == ord('<'):
                v = u + 1
                if lower[v] < next_value:
                    lower[v] = next_value

                indegree[v] -= 1
                if indegree[v] == 0:
                    queue.append(v)

        if len(queue) != M:
            answers.append("NO")
            continue

        for i, value in enumerate(fixed):
            if value != -1 and lower[i] != value:
                ok = False
                break

        answers.append("YES" if ok else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()