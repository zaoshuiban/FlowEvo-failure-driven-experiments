import sys
from array import array

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    n = data[0]
    b = data[1:]

    max_v = max(b)

    spf = array('I', range(max_v + 1))
    if max_v >= 1:
        spf[0] = 0
        spf[1] = 1

    limit = int(max_v ** 0.5)
    for i in range(2, limit + 1):
        if spf[i] == i:
            for j in range(i * i, max_v + 1, i):
                if spf[j] == j:
                    spf[j] = i

    prime_index = array('I', [0]) * (max_v + 1)
    prime_count = 0
    for i in range(2, max_v + 1):
        if spf[i] == i:
            prime_count += 1
            prime_index[i] = prime_count

    count = array('I', [0]) * (max_v + 1)
    for x in b:
        count[x] += 1

    answer = []

    for x in range(max_v, 1, -1):
        while count[x] > 0:
            if spf[x] == x:  # x is prime
                idx = prime_index[x]
                count[x] -= 1
                count[idx] -= 1
                answer.append(idx)
            else:  # x is composite
                greatest_divisor = x // spf[x]
                count[x] -= 1
                count[greatest_divisor] -= 1
                answer.append(x)

    print(*answer)

if __name__ == "__main__":
    main()