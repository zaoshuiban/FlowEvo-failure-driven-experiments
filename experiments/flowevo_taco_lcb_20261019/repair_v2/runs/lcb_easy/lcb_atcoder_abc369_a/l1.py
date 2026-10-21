import sys

def main():
    A, B = map(int, sys.stdin.readline().split())

    candidates = set()

    if (A + B) % 2 == 0:
        candidates.add((A + B) // 2)

    candidates.add(2 * A - B)
    candidates.add(2 * B - A)

    print(len(candidates))

if __name__ == "__main__":
    main()