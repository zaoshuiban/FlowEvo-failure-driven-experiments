def main():
    import sys

    S, N_str = sys.stdin.read().split()
    N = int(N_str)
    L = len(S)

    result = []

    for i, ch in enumerate(S):
        if ch != '?':
            result.append(ch)
            continue

        # Try placing 1 at this position, and place 0 in all later '?' positions
        # to get the smallest possible value with this prefix.
        candidate = result + ['1']
        for j in range(i + 1, L):
            if S[j] == '?':
                candidate.append('0')
            else:
                candidate.append(S[j])

        value = int(''.join(candidate), 2)

        if value <= N:
            result.append('1')
        else:
            result.append('0')

    answer = int(''.join(result), 2)

    if answer <= N:
        print(answer)
    else:
        print(-1)


if __name__ == "__main__":
    main()