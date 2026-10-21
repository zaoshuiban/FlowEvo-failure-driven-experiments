import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    probabilities = list(map(float, data[1:1 + n]))
    probabilities.sort(reverse=True)

    prob_one = 0.0
    prob_zero = 1.0
    answer = 0.0

    for p in probabilities:
        prob_one, prob_zero = (
            prob_one * (1.0 - p) + prob_zero * p,
            prob_zero * (1.0 - p)
        )
        answer = max(answer, prob_one)

    print(f"{answer:.15f}")

if __name__ == "__main__":
    main()