import sys
import bisect

def main():
    data = sys.stdin.buffer.read().split()
    N = int(data[0])
    T = int(data[1])
    S = data[2]
    X = list(map(int, data[3:3 + N]))

    ants = [(X[i], S[i]) for i in range(N)]
    ants.sort()

    limit = 2 * T
    right_moving = []
    answer = 0

    for x, direction in ants:
        if direction == ord('1'):
            right_moving.append(x)
        else:
            threshold = x - limit
            idx = bisect.bisect_left(right_moving, threshold)
            answer += len(right_moving) - idx

    print(answer)

if __name__ == "__main__":
    main()