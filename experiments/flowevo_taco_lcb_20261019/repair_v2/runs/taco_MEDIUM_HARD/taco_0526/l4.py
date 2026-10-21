import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    probabilities = list(map(float, data[1:1 + n]))

    probabilities.sort(reverse=True)

    # one: probability of exactly one problem among the chosen friends
    # none: probability of no problems among the chosen friends
    one = 0.0
    none = 1.0
    answer = 0.0

    for p in probabilities:
        one, none = one * (1.0 - p) + none * p, none * (1.0 - p)
        if one > answer:
            answer = one

    print(f"{answer:.15f}")

if __name__ == "__main__":
    main()