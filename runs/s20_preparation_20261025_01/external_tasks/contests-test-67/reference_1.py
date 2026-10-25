import math

def combin(n, m):
    if n == m:
        return 1
    if n < m:
        return 0

    a = 1
    for i in range(n, n-m, -1):
        a *= i
    b = 1
    for i in range(1, m+1):
        b *= i

    return a / b

(a, b) = input().split()
n = int(a)
p = float(b) * combin(n,3)

for i in range(0, n+1):
    ans = combin(i, 3) + combin(i, 2) * combin(n-i, 1)
    ans += (combin(i, 1)*combin(n-i, 2)) / 2

    if ans >= p:
        print(i)
        break