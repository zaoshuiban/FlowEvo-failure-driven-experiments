import sys
from collections import deque

INF = 10 ** 9


def solve_case(H, K, arr):
    N = 1 << H
    limak = arr[0]

    ans = 0
    possible = True

    def update_costs(cand_x, cand_c, opp_x, opp_c):
        nc = len(cand_x)
        no = len(opp_x)

        res = [INF] * nc
        dq = deque()

        add_ptr = 0
        rem_ptr = 0
        less_ptr = 0
        prefix_min = INF

        for i in range(nc):
            x = cand_x[i]

            while less_ptr < no and opp_x[less_ptr] < x:
                v = opp_c[less_ptr]
                if v < prefix_min:
                    prefix_min = v
                less_ptr += 1

            upper = x + K
            while add_ptr < no and opp_x[add_ptr] <= upper:
                v = opp_c[add_ptr]
                while dq and opp_c[dq[-1]] >= v:
                    dq.pop()
                dq.append(add_ptr)
                add_ptr += 1

            while rem_ptr < no and opp_x[rem_ptr] <= x:
                rem_ptr += 1

            while dq and dq[0] < rem_ptr:
                dq.popleft()

            best = prefix_min

            if dq:
                v = opp_c[dq[0]] + 1
                if v < best:
                    best = v

            c = cand_c[i]
            if c < INF and best < INF:
                res[i] = c + best

        return res

    def merge_sorted(lx, lc, rx, rc):
        n1 = len(lx)
        n2 = len(rx)

        xs = [0] * (n1 + n2)
        cs = [0] * (n1 + n2)

        i = j = idx = 0

        while i < n1 and j < n2:
            if lx[i] < rx[j]:
                xs[idx] = lx[i]
                cs[idx] = lc[i]
                i += 1
            else:
                xs[idx] = rx[j]
                cs[idx] = rc[j]
                j += 1
            idx += 1

        while i < n1:
            xs[idx] = lx[i]
            cs[idx] = lc[i]
            i += 1
            idx += 1

        while j < n2:
            xs[idx] = rx[j]
            cs[idx] = rc[j]
            j += 1
            idx += 1

        return xs, cs

    def dfs(left, right):
        nonlocal ans, possible

        if left == right:
            return [arr[left]], [0]

        mid = (left + right) // 2

        left_x, left_c = dfs(left, mid)
        right_x, right_c = dfs(mid + 1, right)

        new_left_c = update_costs(left_x, left_c, right_x, right_c)
        new_right_c = update_costs(right_x, right_c, left_x, left_c)

        xs, cs = merge_sorted(left_x, new_left_c, right_x, new_right_c)

        length = right - left + 1

        # These are exactly the sibling blocks on Limak's path:
        # [1,1], [2,3], [4,7], ... in 0-based indexing.
        if left == length:
            best = INF

            for i in range(length):
                strength = xs[i]
                cost = cs[i]

                if cost >= INF:
                    continue

                if strength < limak:
                    value = cost
                else:
                    if strength - limak <= K:
                        value = cost + 1
                    else:
                        continue

                if value < best:
                    best = value

            if best >= INF:
                possible = False
            else:
                ans += best

        return xs, cs

    dfs(0, N - 1)

    return ans if possible else -1


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    answers = []

    for _ in range(T):
        H = next(it)
        K = next(it)
        N = 1 << H
        arr = [next(it) for _ in range(N)]

        answers.append(str(solve_case(H, K, arr)))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()