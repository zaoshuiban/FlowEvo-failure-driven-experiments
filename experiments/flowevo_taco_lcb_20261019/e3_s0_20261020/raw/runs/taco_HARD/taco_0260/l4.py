import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    idx = 2

    heroes = []
    for _ in range(m):
        s = data[idx] - 1
        h = data[idx + 1]
        idx += 2
        heroes.append((s, h))

    a = data[idx:idx + n]

    # right_ok[i][e] = hero i can move right from s_i+1 through e
    # left_ok[i][e]  = hero i can move left from s_i-1 down to e
    right_ok = []
    left_ok = []

    for s, h in heroes:
        ok = [False] * n
        hp = h
        ok[s] = True
        for e in range(s + 1, n):
            if not ok[e - 1]:
                ok[e] = False
            else:
                hp += a[e]
                ok[e] = hp >= 0
        right_ok.append(ok)

        ok = [False] * n
        hp = h
        ok[s] = True
        for e in range(s - 1, -1, -1):
            if not ok[e + 1]:
                ok[e] = False
            else:
                hp += a[e]
                ok[e] = hp >= 0
        left_ok.append(ok)

    for t in range(n):
        goodL = [False] * n
        parentL = [-1] * n

        for L in range(0, t + 1):
            any_outside = False
            possible = False
            parent = -1

            for i, (s, _) in enumerate(heroes):
                if s < L:
                    any_outside = True
                    if right_ok[i][L - 1] and goodL[s]:
                        possible = True
                        parent = i
                        break

            if not any_outside:
                possible = True
                parent = -1

            goodL[L] = possible
            parentL[L] = parent if possible else -1

        goodR = [False] * n
        parentR = [-1] * n

        for R in range(n - 1, t - 1, -1):
            any_outside = False
            possible = False
            parent = -1

            for i, (s, _) in enumerate(heroes):
                if s > R:
                    any_outside = True
                    if left_ok[i][R + 1] and goodR[s]:
                        possible = True
                        parent = i
                        break

            if not any_outside:
                possible = True
                parent = -1

            goodR[R] = possible
            parentR[R] = parent if possible else -1

        def get_left_sequence(L):
            seq = []
            while 0 <= L < n:
                i = parentL[L]
                if i == -1:
                    break
                seq.append(i)
                L = heroes[i][0]
            return seq

        def get_right_sequence(R):
            seq = []
            while 0 <= R < n:
                i = parentR[R]
                if i == -1:
                    break
                seq.append(i)
                R = heroes[i][0]
            return seq

        order = None

        if a[t] == 0:
            if goodL[t] and goodR[t]:
                order = []
                order.extend(get_left_sequence(t))
                order.extend(get_right_sequence(t))
        else:
            # The first hero comes from the left and reaches the rally point t.
            if goodR[t]:
                for i, (s, _) in enumerate(heroes):
                    if s < t and right_ok[i][t] and goodL[s]:
                        order = [i]
                        order.extend(get_left_sequence(s))
                        order.extend(get_right_sequence(t))
                        break

            # The first hero comes from the right and reaches the rally point t.
            if order is None and goodL[t]:
                for i, (s, _) in enumerate(heroes):
                    if s > t and left_ok[i][t] and goodR[s]:
                        order = [i]
                        order.extend(get_right_sequence(s))
                        order.extend(get_left_sequence(t))
                        break

        if order is not None:
            used = [False] * m
            final_order = []

            for i in order:
                if not used[i]:
                    used[i] = True
                    final_order.append(i)

            for i in range(m):
                if not used[i]:
                    final_order.append(i)

            print(t + 1)
            print(" ".join(str(i + 1) for i in final_order))
            return

    print(-1)


if __name__ == "__main__":
    main()