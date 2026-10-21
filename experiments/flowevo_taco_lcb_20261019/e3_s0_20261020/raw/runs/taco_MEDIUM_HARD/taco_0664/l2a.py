import sys
from collections import deque


def solve_case(N, K, P, A, ops):
    total = sum(A)

    if K >= N:
        return [str(total)] * ops.count(b'?')

    a2 = A + A

    # W[i] = sum of K consecutive elements starting at i in A+A
    M = 2 * N - K
    W = [0] * M

    current = sum(a2[:K])
    W[0] = current

    for i in range(1, M):
        current += a2[i + K - 1] - a2[i - 1]
        W[i] = current

    # ans[c] = answer when the rotated array starts at original index c
    ans = [0] * N
    window_len = N - K + 1

    dq = deque()

    for i in range(M):
        while dq and W[dq[-1]] <= W[i]:
            dq.pop()
        dq.append(i)

        c = i - window_len + 1

        if c >= 0:
            while dq and dq[0] < c:
                dq.popleft()
            ans[c] = W[dq[0]]

    result = []
    start = 0

    for ch in ops:
        if ch == ord('!'):
            start -= 1
            if start < 0:
                start += N
        elif ch == ord('?'):
            result.append(str(ans[start]))

    return result


def main():
    inp = sys.stdin.buffer

    first = inp.readline()
    while first and not first.strip():
        first = inp.readline()

    if not first:
        return

    first_parts = first.split()
    output = []

    # Supports both the described single-test-case format and a possible T-based format.
    if len(first_parts) == 3:
        N, K, P = map(int, first_parts)
        rest = inp.read().split()

        A = list(map(int, rest[:N]))

        if P > 0 and len(rest) > N:
            ops = rest[N]
        else:
            ops = b''

        output.extend(solve_case(N, K, P, A, ops))

    else:
        T = int(first_parts[0])
        tokens = inp.read().split()
        idx = 0

        for _ in range(T):
            N = int(tokens[idx])
            K = int(tokens[idx + 1])
            P = int(tokens[idx + 2])
            idx += 3

            A = list(map(int, tokens[idx:idx + N]))
            idx += N

            if P > 0:
                ops = tokens[idx]
                idx += 1
            else:
                ops = b''

            output.extend(solve_case(N, K, P, A, ops))

    sys.stdout.write('\n'.join(output))


if __name__ == "__main__":
    main()