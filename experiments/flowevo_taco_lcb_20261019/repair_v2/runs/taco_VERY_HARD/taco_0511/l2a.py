import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    T = data[idx]
    idx += 1

    answers = []

    for _ in range(T):
        N = data[idx]
        K = data[idx + 1]
        idx += 2

        A = data[idx:idx + N]
        idx += N

        S = data[idx:idx + K]
        idx += K

        max_pos = 0
        max_val = A[0]

        for i in range(1, N):
            if A[i] > max_val:
                max_val = A[i]
                max_pos = i

        # Number of discs before the maximum disc.
        Lmax = max_pos

        # Number of remaining discs from the maximum disc to the bottom.
        tail = N - max_pos

        # dp[L] = True if the player to move can force getting the maximum disc
        # when there are L discs before it.
        dp = [False] * (Lmax + 1)

        for L in range(Lmax + 1):
            upper = L + tail
            win = False

            # Current player can directly take the maximum disc.
            for x in S:
                if L < x <= upper:
                    win = True
                    break

            # Otherwise, try to leave a losing position to the opponent.
            if not win:
                for x in S:
                    if x <= L and not dp[L - x]:
                        win = True
                        break

            dp[L] = win

        answers.append("Chef" if dp[Lmax] else "Garry")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()