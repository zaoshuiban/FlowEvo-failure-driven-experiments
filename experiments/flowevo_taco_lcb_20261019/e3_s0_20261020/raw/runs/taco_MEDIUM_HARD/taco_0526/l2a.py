import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    probabilities = list(map(float, data[1:1 + n]))
    probabilities.sort(reverse=True)

    exactly_one = 0.0
    none = 1.0
    answer = 0.0

    for p in probabilities:
        new_exactly_one = exactly_one * (1.0 - p) + none * p
        new_none = none * (1.0 - p)

        exactly_one = new_exactly_one
        none = new_none

        if exactly_one > answer:
            answer = exactly_one

    print(f"{answer:.12f}")

if __name__ == "__main__":
    main()