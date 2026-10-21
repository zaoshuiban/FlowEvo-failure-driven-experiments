import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a = data[1:4]  # Alice: rock, scissors, paper
    b = data[4:7]  # Bob: rock, scissors, paper

    # Maximum wins:
    # Alice rock beats Bob scissors
    # Alice scissors beats Bob paper
    # Alice paper beats Bob rock
    max_wins = (
        min(a[0], b[1]) +
        min(a[1], b[2]) +
        min(a[2], b[0])
    )

    # Non-winning Bob choices for each Alice choice:
    # Alice rock: Bob rock/paper -> indices 0,2
    # Alice scissors: Bob scissors/rock -> indices 1,0
    # Alice paper: Bob paper/scissors -> indices 2,1
    non_winning_masks = [
        (1 << 0) | (1 << 2),
        (1 << 1) | (1 << 0),
        (1 << 2) | (1 << 1)
    ]

    min_wins = 0

    # Check every subset of Alice choices using the matching deficit formula.
    for alice_mask in range(8):
        alice_sum = 0
        bob_mask = 0

        for i in range(3):
            if alice_mask & (1 << i):
                alice_sum += a[i]
                bob_mask |= non_winning_masks[i]

        bob_sum = 0
        for j in range(3):
            if bob_mask & (1 << j):
                bob_sum += b[j]

        min_wins = max(min_wins, alice_sum - bob_sum)

    print(min_wins, max_wins)


if __name__ == "__main__":
    solve()