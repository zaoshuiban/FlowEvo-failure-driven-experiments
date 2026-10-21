import sys

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    N, K = data[0], data[1]
    A = data[2:2 + N]

    present = {x for x in A if x <= K}
    total = K * (K + 1) // 2
    answer = total - sum(present)

    print(answer)

if __name__ == "__main__":
    main()