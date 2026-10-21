import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]

    groups = {}
    idx = 1

    for _ in range(n):
        s = data[idx]
        c = data[idx + 1]
        idx += 2

        lowbit = s & -s
        odd_part = s // lowbit

        groups[odd_part] = groups.get(odd_part, 0) + c * lowbit

    answer = sum(value.bit_count() for value in groups.values())
    print(answer)

if __name__ == "__main__":
    main()