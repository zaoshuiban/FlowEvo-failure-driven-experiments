import sys

def main():
    input = sys.stdin.readline

    N, M = map(int, input().split())
    S = [input().strip() for _ in range(N)]

    ans = []

    for r in range(N - 8):
        for c in range(M - 8):
            ok = True

            # Top-left 3x3 must be black
            for dr in range(3):
                for dc in range(3):
                    if S[r + dr][c + dc] != '#':
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue

            # Bottom-right 3x3 must be black
            for dr in range(6, 9):
                for dc in range(6, 9):
                    if S[r + dr][c + dc] != '#':
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue

            # Cells adjacent to the top-left 3x3 must be white
            for dc in range(4):
                if S[r + 3][c + dc] != '.':
                    ok = False
                    break
            if not ok:
                continue

            for dr in range(3):
                if S[r + dr][c + 3] != '.':
                    ok = False
                    break
            if not ok:
                continue

            # Cells adjacent to the bottom-right 3x3 must be white
            for dc in range(5, 9):
                if S[r + 5][c + dc] != '.':
                    ok = False
                    break
            if not ok:
                continue

            for dr in range(6, 9):
                if S[r + dr][c + 5] != '.':
                    ok = False
                    break
            if not ok:
                continue

            ans.append((r + 1, c + 1))

    for i, j in ans:
        print(i, j)


if __name__ == "__main__":
    main()