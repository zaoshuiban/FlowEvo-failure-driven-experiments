import sys
from functools import lru_cache

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, M, L = data[0], data[1], data[2]

    idx = 3
    A = data[idx:idx + N]
    idx += N
    B = data[idx:idx + M]
    idx += M
    C = data[idx:idx + L]

    values = A + B + C
    K = N + M + L
    full = (1 << K) - 1

    less_mask = [0] * K
    for i in range(K):
        mask = 0
        for j in range(K):
            if values[j] < values[i]:
                mask |= 1 << j
        less_mask[i] = mask

    initial_takahashi = (1 << N) - 1
    initial_aoki = ((1 << M) - 1) << N

    sys.setrecursionlimit(1_000_000)

    @lru_cache(maxsize=None)
    def win(my_hand, opponent_hand):
        if my_hand == 0:
            return False

        table = full ^ (my_hand | opponent_hand)
        bits = my_hand

        while bits:
            card_bit = bits & -bits
            bits ^= card_bit
            card_index = card_bit.bit_length() - 1

            next_my_hand = my_hand ^ card_bit

            if not win(opponent_hand, next_my_hand):
                return True

            take_candidates = table & less_mask[card_index]
            while take_candidates:
                take_bit = take_candidates & -take_candidates
                take_candidates ^= take_bit

                next_my_hand_with_take = next_my_hand | take_bit
                if not win(opponent_hand, next_my_hand_with_take):
                    return True

        return False

    if win(initial_takahashi, initial_aoki):
        print("Takahashi")
    else:
        print("Aoki")


if __name__ == "__main__":
    main()