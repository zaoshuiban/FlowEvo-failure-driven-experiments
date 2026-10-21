import sys


def main():
    data = sys.stdin.read().split()
    it = iter(data)

    HA = int(next(it))
    WA = int(next(it))
    A = [next(it) for _ in range(HA)]

    HB = int(next(it))
    WB = int(next(it))
    B = [next(it) for _ in range(HB)]

    HX = int(next(it))
    WX = int(next(it))
    X = [next(it) for _ in range(HX)]

    A_black = [
        (i, j)
        for i in range(HA)
        for j in range(WA)
        if A[i][j] == '#'
    ]

    B_black = [
        (i, j)
        for i in range(HB)
        for j in range(WB)
        if B[i][j] == '#'
    ]

    X_set = {
        (i, j)
        for i in range(HX)
        for j in range(WX)
        if X[i][j] == '#'
    }

    for ay in range(-HA + 1, HX):
        for ax in range(-WA + 1, WX):
            cells_a = []
            ok = True

            for i, j in A_black:
                y = ay + i
                x = ax + j

                if not (0 <= y < HX and 0 <= x < WX):
                    ok = False
                    break

                cells_a.append((y, x))

            if not ok:
                continue

            for by in range(-HB + 1, HX):
                for bx in range(-WB + 1, WX):
                    union = set(cells_a)
                    ok_b = True

                    for i, j in B_black:
                        y = by + i
                        x = bx + j

                        if not (0 <= y < HX and 0 <= x < WX):
                            ok_b = False
                            break

                        union.add((y, x))

                    if ok_b and union == X_set:
                        print("Yes")
                        return

    print("No")


if __name__ == "__main__":
    main()