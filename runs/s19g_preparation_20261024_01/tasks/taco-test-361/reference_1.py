import math
(r, x, y, a, b) = map(int, input().split())
d = math.sqrt((a - x) ** 2 + (b - y) ** 2)
print(math.ceil(d / (2 * r)))
