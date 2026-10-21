import sys

def solve() -> None:
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    k = int(data[1])

    damages = list(map(int, data[2:2 + n]))
    s = data[2 + n]

    answer = 0
    i = 0

    while i < n:
        j = i
        values = []

        while j < n and s[j] == s[i]:
            values.append(damages[j])
            j += 1

        if len(values) <= k:
            answer += sum(values)
        else:
            values.sort(reverse=True)
            answer += sum(values[:k])

        i = j

    print(answer)


if __name__ == "__main__":
    solve()