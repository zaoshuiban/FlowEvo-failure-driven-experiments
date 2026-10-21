import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    a1, a2, a3 = data[1], data[2], data[3]  # Alice: rock, scissors, paper
    b1, b2, b3 = data[4], data[5], data[6]  # Bob: rock, scissors, paper

    # Minimum wins: unavoidable wins for each of Alice's choices.
    min_wins = max(
        0,
        a1 - b1 - b3,  # Alice's rock cannot win against Bob's rock or paper
        a2 - b2 - b1,  # Alice's scissors cannot win against Bob's scissors or rock
        a3 - b3 - b2   # Alice's paper cannot win against Bob's paper or scissors
    )

    # Maximum wins: independently match each winning pair.
    max_wins = (
        min(a1, b2) +  # rock beats scissors
        min(a2, b3) +  # scissors beats paper
        min(a3, b1)    # paper beats rock
    )

    print(min_wins, max_wins)


if __name__ == "__main__":
    solve()