import math
(r, x, y, p, q) = list(map(int, input().strip().split(' ')))
print(math.ceil(((p - x) ** 2 + (q - y) ** 2) ** 0.5 / (2 * r)))
