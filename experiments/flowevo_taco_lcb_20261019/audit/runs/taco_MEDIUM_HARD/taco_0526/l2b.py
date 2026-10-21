import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    probs = [float(x) for x in data[1:n + 1]]
    probs.sort(reverse=True)

    ans = 0.0          # probability of exactly one problem
    zero = 1.0         # probability of zero problems

    for p in probs:
        new_ans = ans * (1.0 - p) + zero * p

        if new_ans > ans:
            ans = new_ans
            zero *= (1.0 - p)
        else:
            break

    print(f"{ans:.12f}")

if __name__ == "__main__":
    main()