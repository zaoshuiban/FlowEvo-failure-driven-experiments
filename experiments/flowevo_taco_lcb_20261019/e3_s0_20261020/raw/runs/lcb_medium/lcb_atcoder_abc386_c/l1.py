import sys

def main():
    data = sys.stdin.buffer.read().split()
    K = int(data[0])
    S = data[1]
    T = data[2]

    if K == 0:
        print("Yes" if S == T else "No")
        return

    n, m = len(S), len(T)

    if abs(n - m) > 1:
        print("No")
        return

    if n == m:
        diff = 0
        for a, b in zip(S, T):
            if a != b:
                diff += 1
                if diff > 1:
                    print("No")
                    return
        print("Yes")
        return

    if n > m:
        S, T = T, S
        n, m = m, n

    i = 0
    while i < n and S[i] == T[i]:
        i += 1

    if S[i:] == T[i + 1:]:
        print("Yes")
    else:
        print("No")


if __name__ == "__main__":
    main()