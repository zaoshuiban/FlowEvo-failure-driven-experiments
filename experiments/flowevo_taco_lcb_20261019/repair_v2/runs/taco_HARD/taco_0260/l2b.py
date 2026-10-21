import sys


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    pos = 2

    hero_id_at = [0] * (n + 2)
    hero_hp = [0] * (n + 2)

    for i in range(1, m + 1):
        s = data[pos]
        h = data[pos + 1]
        pos += 2
        hero_id_at[s] = i
        hero_hp[s] = h

    a = [0] + data[pos:pos + n]

    prefix_hero = [0] * (n + 2)
    for i in range(1, n + 1):
        prefix_hero[i] = prefix_hero[i - 1] + (1 if hero_id_at[i] != 0 else 0)

    # can_left[x][b]: hero starting at x can survive moving right
    # through cells x ... b-1.
    can_left = [[False] * (n + 2) for _ in range(n + 2)]
    can_right = [[False] * (n + 2) for _ in range(n + 2)]

    for s in range(1, n + 1):
        if hero_id_at[s] == 0:
            continue

        hp = hero_hp[s]
        ok = True
        can_left[s][s] = True

        for b in range(s + 1, n + 2):
            if ok:
                val = a[b - 1]
                if val < 0:
                    if hp < -val:
                        ok = False
                    else:
                        hp += val
                elif val > 0:
                    hp += val
            can_left[s][b] = ok

        hp = hero_hp[s]
        ok = True
        can_right[s][s] = True

        for b in range(s - 1, 0, -1):
            if ok:
                val = a[b + 1]
                if val < 0:
                    if hp < -val:
                        ok = False
                    else:
                        hp += val
                elif val > 0:
                    hp += val
            can_right[s][b] = ok

    def can_first_left(x, p):
        hp = hero_hp[x]
        for cell in range(x, p + 1):
            val = a[cell]
            if val < 0:
                if hp < -val:
                    return False
                hp += val
            elif val > 0:
                hp += val
        return True

    def can_first_right(x, p):
        hp = hero_hp[x]
        for cell in range(x, p - 1, -1):
            val = a[cell]
            if val < 0:
                if hp < -val:
                    return False
                hp += val
            elif val > 0:
                hp += val
        return True

    answer_p = -1
    first_pos = 0
    first_side = 0  # 0 = none, 1 = left, 2 = right

    dpL = parL = dpR = parR = None

    for p in range(1, n + 1):
        dpL = [False] * (n + 2)
        parL = [0] * (n + 2)

        for b in range(1, p + 1):
            if prefix_hero[b - 1] == 0:
                dpL[b] = True
            else:
                for x in range(1, b):
                    if hero_id_at[x] != 0 and dpL[x] and can_left[x][b]:
                        dpL[b] = True
                        parL[b] = x
                        break

        dpR = [False] * (n + 2)
        parR = [0] * (n + 2)

        for b in range(n, p - 1, -1):
            if m - prefix_hero[b] == 0:
                dpR[b] = True
            else:
                for x in range(b + 1, n + 1):
                    if hero_id_at[x] != 0 and dpR[x] and can_right[x][b]:
                        dpR[b] = True
                        parR[b] = x
                        break

        if a[p] == 0:
            if dpL[p] and dpR[p]:
                answer_p = p
                first_pos = 0
                first_side = 0
                break
        else:
            feasible = False

            if dpR[p]:
                for x in range(1, p):
                    if hero_id_at[x] != 0 and dpL[x] and can_first_left(x, p):
                        answer_p = p
                        first_pos = x
                        first_side = 1
                        feasible = True
                        break

            if not feasible and dpL[p]:
                for x in range(p + 1, n + 1):
                    if hero_id_at[x] != 0 and dpR[x] and can_first_right(x, p):
                        answer_p = p
                        first_pos = x
                        first_side = 2
                        feasible = True
                        break

            if feasible:
                break

    if answer_p == -1:
        print(-1)
        return

    used = [False] * (m + 1)
    order = []

    def add_pos(cell):
        idx = hero_id_at[cell]
        if idx != 0 and not used[idx]:
            used[idx] = True
            order.append(idx)

    if first_side == 0:
        b = answer_p
        while parL[b] != 0:
            x = parL[b]
            add_pos(x)
            b = x

        b = answer_p
        while parR[b] != 0:
            x = parR[b]
            add_pos(x)
            b = x

    elif first_side == 1:
        add_pos(first_pos)

        b = first_pos
        while parL[b] != 0:
            x = parL[b]
            add_pos(x)
            b = x

        b = answer_p
        while parR[b] != 0:
            x = parR[b]
            add_pos(x)
            b = x

    else:
        add_pos(first_pos)

        b = first_pos
        while parR[b] != 0:
            x = parR[b]
            add_pos(x)
            b = x

        b = answer_p
        while parL[b] != 0:
            x = parL[b]
            add_pos(x)
            b = x

    for i in range(1, m + 1):
        if not used[i]:
            order.append(i)

    print(answer_p)
    print(*order)


if __name__ == "__main__":
    solve()